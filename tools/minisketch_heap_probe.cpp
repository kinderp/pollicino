#include <minisketch.h>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <new>

namespace {
struct alignas(std::max_align_t) AllocationHeader {
    std::size_t size;
};

std::size_t g_current = 0;
std::size_t g_peak = 0;

void* tracked_allocate(std::size_t size) {
    const std::size_t total = sizeof(AllocationHeader) + size;
    void* raw = std::malloc(total);
    if (!raw) throw std::bad_alloc();
    auto* header = static_cast<AllocationHeader*>(raw);
    header->size = size;
    g_current += size;
    g_peak = std::max(g_peak, g_current);
    return header + 1;
}

void tracked_free(void* ptr) noexcept {
    if (!ptr) return;
    auto* header = static_cast<AllocationHeader*>(ptr) - 1;
    if (header->size > g_current) std::abort();
    g_current -= header->size;
    std::free(header);
}

void reset_peak() { g_peak = g_current; }

struct Phase {
    std::size_t before;
    std::size_t after;
    std::size_t peak;
};

Phase finish_phase(std::size_t before) {
    return Phase{before, g_current, g_peak};
}

void print_phase(const char* name, const Phase& p) {
    const long long retained = static_cast<long long>(p.after) - static_cast<long long>(p.before);
    const long long peak_extra = static_cast<long long>(p.peak) - static_cast<long long>(p.before);
    std::printf("%s_retained=%lld %s_peak_extra=%lld\n", name, retained, name, peak_extra);
}

void add_set(minisketch* sketch, std::size_t common_count, std::size_t unique_start, std::size_t unique_count) {
    for (std::size_t i = 1; i <= common_count; ++i) {
        minisketch_add_uint64(sketch, i);
    }
    for (std::size_t i = 0; i < unique_count; ++i) {
        minisketch_add_uint64(sketch, unique_start + i);
    }
}

void run_case(std::size_t capacity, std::size_t common_count, std::size_t unique_each) {
    const std::size_t baseline = g_current;

    // SOURCE persistent local sketch.
    reset_peak();
    minisketch* source = minisketch_create(16, 0, capacity);
    const Phase create_source = finish_phase(baseline);
    if (!source) std::abort();
    minisketch_set_seed(source, UINT64_MAX);

    reset_peak();
    const std::size_t before_add_source = g_current;
    add_set(source, common_count, common_count + 1, unique_each);
    const Phase add_source = finish_phase(before_add_source);

    // RECEIVER builds and serializes on its own logical device. We measure this
    // phase, then destroy it before measuring SOURCE-side remote+decode memory.
    reset_peak();
    const std::size_t before_receiver_create = g_current;
    minisketch* receiver = minisketch_create(16, 0, capacity);
    const Phase create_receiver = finish_phase(before_receiver_create);
    if (!receiver) std::abort();
    minisketch_set_seed(receiver, UINT64_MAX);

    reset_peak();
    const std::size_t before_add_receiver = g_current;
    add_set(receiver, common_count, common_count + unique_each + 1, unique_each);
    const Phase add_receiver = finish_phase(before_add_receiver);

    const std::size_t serialized_size = minisketch_serialized_size(receiver);
    unsigned char* serialized = static_cast<unsigned char*>(std::malloc(serialized_size));
    if (!serialized) std::abort();

    reset_peak();
    const std::size_t before_serialize = g_current;
    minisketch_serialize(receiver, serialized);
    const Phase serialize = finish_phase(before_serialize);
    minisketch_destroy(receiver);

    // SOURCE receives/deserializes the receiver sketch. From here on only the
    // source's local sketch and one remote sketch coexist on this logical node.
    reset_peak();
    const std::size_t before_remote_create = g_current;
    minisketch* remote = minisketch_create(16, 0, capacity);
    const Phase create_remote = finish_phase(before_remote_create);
    if (!remote) std::abort();
    minisketch_set_seed(remote, UINT64_MAX);
    minisketch_deserialize(remote, serialized);
    const std::size_t two_source_side_sketches_retained = g_current - baseline;

    reset_peak();
    const std::size_t before_merge = g_current;
    if (minisketch_merge(source, remote) == 0) std::abort();
    const Phase merge = finish_phase(before_merge);

    uint64_t* decoded = static_cast<uint64_t*>(std::malloc(sizeof(uint64_t) * capacity));
    if (!decoded) std::abort();
    reset_peak();
    const std::size_t before_decode = g_current;
    const ssize_t decoded_count = minisketch_decode(source, capacity, decoded);
    const Phase decode = finish_phase(before_decode);

    std::printf("CASE capacity=%zu common=%zu unique_each=%zu serialized=%zu decoded=%zd\n",
                capacity, common_count, unique_each, serialized_size, decoded_count);
    print_phase("create_source", create_source);
    print_phase("add_source", add_source);
    print_phase("create_receiver", create_receiver);
    print_phase("add_receiver", add_receiver);
    print_phase("serialize", serialize);
    print_phase("create_remote", create_remote);
    print_phase("merge", merge);
    print_phase("decode", decode);
    std::printf("source_side_two_sketches_retained=%zu\n", two_source_side_sketches_retained);

    std::free(decoded);
    std::free(serialized);
    minisketch_destroy(remote);
    minisketch_destroy(source);
    std::printf("after_destroy_delta=%lld\n",
                static_cast<long long>(g_current) - static_cast<long long>(baseline));
}
}  // namespace

void* operator new(std::size_t size) { return tracked_allocate(size); }
void* operator new[](std::size_t size) { return tracked_allocate(size); }
void operator delete(void* ptr) noexcept { tracked_free(ptr); }
void operator delete[](void* ptr) noexcept { tracked_free(ptr); }
void operator delete(void* ptr, std::size_t) noexcept { tracked_free(ptr); }
void operator delete[](void* ptr, std::size_t) noexcept { tracked_free(ptr); }

int main() {
    if (!minisketch_bits_supported(16) || !minisketch_implementation_supported(16, 0)) {
        std::fprintf(stderr, "generic 16-bit minisketch unavailable\n");
        return 2;
    }

    // Pollicino's discriminating current case: 50,000 common chunks and ten
    // unique chunks per peer, actual symmetric difference 20, capacity 32.
    run_case(32, 50000, 10);

    // Capacity-scaling probes keep the same 20-element difference while
    // over-provisioning the sketch, matching the earlier wire-budget research.
    for (std::size_t capacity : {64u, 128u, 256u, 512u, 1024u}) {
        run_case(capacity, 1000, 10);
    }
    return 0;
}
