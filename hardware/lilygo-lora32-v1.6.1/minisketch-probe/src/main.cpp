#include <Arduino.h>
#include <esp_heap_caps.h>
#include <esp_timer.h>
#include <minisketch.h>

#include <algorithm>
#include <cstdint>
#include <cstdlib>

namespace {
constexpr uint32_t BITS = 16;
constexpr uint32_t IMPLEMENTATION = 0;
constexpr size_t COMMON_COUNT = 50000;
constexpr size_t UNIQUE_EACH = 10;
constexpr size_t EXPECTED_DIFF = 20;
constexpr size_t TRIALS = 5;

struct HeapSnapshot {
  uint32_t free_heap;
  uint32_t min_free_heap;
  uint32_t largest_block;
};

HeapSnapshot heapSnapshot() {
  return HeapSnapshot{
      ESP.getFreeHeap(),
      ESP.getMinFreeHeap(),
      static_cast<uint32_t>(heap_caps_get_largest_free_block(MALLOC_CAP_8BIT)),
  };
}

void printHeap(const char* prefix, const HeapSnapshot& h) {
  Serial.printf(
      "%s free=%u min_free=%u largest=%u\n",
      prefix,
      h.free_heap,
      h.min_free_heap,
      h.largest_block);
}

void addSourceSet(minisketch* sketch) {
  for (uint64_t element = 1; element <= COMMON_COUNT; ++element) {
    minisketch_add_uint64(sketch, element);
  }
  for (uint64_t element = COMMON_COUNT + 1;
       element <= COMMON_COUNT + UNIQUE_EACH;
       ++element) {
    minisketch_add_uint64(sketch, element);
  }
}

void addReceiverSet(minisketch* sketch) {
  for (uint64_t element = 1; element <= COMMON_COUNT; ++element) {
    minisketch_add_uint64(sketch, element);
  }
  for (uint64_t element = COMMON_COUNT + UNIQUE_EACH + 1;
       element <= COMMON_COUNT + 2 * UNIQUE_EACH;
       ++element) {
    minisketch_add_uint64(sketch, element);
  }
}

bool isExpectedDifference(const uint64_t* decoded, ssize_t count) {
  if (count != static_cast<ssize_t>(EXPECTED_DIFF)) return false;
  bool seen[EXPECTED_DIFF] = {};
  for (ssize_t i = 0; i < count; ++i) {
    const uint64_t value = decoded[i];
    if (value < COMMON_COUNT + 1 || value > COMMON_COUNT + 2 * UNIQUE_EACH) {
      return false;
    }
    const size_t position = static_cast<size_t>(value - (COMMON_COUNT + 1));
    if (position >= EXPECTED_DIFF || seen[position]) return false;
    seen[position] = true;
  }
  return std::all_of(std::begin(seen), std::end(seen), [](bool value) { return value; });
}

void runTrial(size_t capacity, size_t trial) {
  const HeapSnapshot start_heap = heapSnapshot();

  int64_t t0 = esp_timer_get_time();
  minisketch* receiver = minisketch_create(BITS, IMPLEMENTATION, capacity);
  const int64_t receiver_create_us = esp_timer_get_time() - t0;
  if (!receiver) {
    Serial.printf("MSP_FAIL capacity=%u trial=%u phase=receiver_create\n",
                  static_cast<unsigned>(capacity), static_cast<unsigned>(trial));
    return;
  }
  minisketch_set_seed(receiver, UINT64_MAX);
  const HeapSnapshot receiver_created_heap = heapSnapshot();

  t0 = esp_timer_get_time();
  addReceiverSet(receiver);
  const int64_t receiver_build_us = esp_timer_get_time() - t0;
  const HeapSnapshot receiver_built_heap = heapSnapshot();

  const size_t serialized_size = minisketch_serialized_size(receiver);
  uint8_t* serialized = static_cast<uint8_t*>(malloc(serialized_size));
  if (!serialized) {
    minisketch_destroy(receiver);
    Serial.printf("MSP_FAIL capacity=%u trial=%u phase=serialize_alloc bytes=%u\n",
                  static_cast<unsigned>(capacity), static_cast<unsigned>(trial),
                  static_cast<unsigned>(serialized_size));
    return;
  }
  t0 = esp_timer_get_time();
  minisketch_serialize(receiver, serialized);
  const int64_t serialize_us = esp_timer_get_time() - t0;
  minisketch_destroy(receiver);
  const HeapSnapshot after_receiver_destroy = heapSnapshot();

  t0 = esp_timer_get_time();
  minisketch* source = minisketch_create(BITS, IMPLEMENTATION, capacity);
  const int64_t source_create_us = esp_timer_get_time() - t0;
  if (!source) {
    free(serialized);
    Serial.printf("MSP_FAIL capacity=%u trial=%u phase=source_create\n",
                  static_cast<unsigned>(capacity), static_cast<unsigned>(trial));
    return;
  }
  minisketch_set_seed(source, UINT64_MAX);

  t0 = esp_timer_get_time();
  addSourceSet(source);
  const int64_t source_build_us = esp_timer_get_time() - t0;

  minisketch* remote = minisketch_create(BITS, IMPLEMENTATION, capacity);
  if (!remote) {
    minisketch_destroy(source);
    free(serialized);
    Serial.printf("MSP_FAIL capacity=%u trial=%u phase=remote_create\n",
                  static_cast<unsigned>(capacity), static_cast<unsigned>(trial));
    return;
  }
  minisketch_set_seed(remote, UINT64_MAX);
  minisketch_deserialize(remote, serialized);
  const HeapSnapshot before_decode_heap = heapSnapshot();

  t0 = esp_timer_get_time();
  const size_t merged_capacity = minisketch_merge(source, remote);
  const int64_t merge_us = esp_timer_get_time() - t0;

  uint64_t* decoded = static_cast<uint64_t*>(malloc(sizeof(uint64_t) * capacity));
  if (!decoded) {
    minisketch_destroy(remote);
    minisketch_destroy(source);
    free(serialized);
    Serial.printf("MSP_FAIL capacity=%u trial=%u phase=decode_alloc bytes=%u\n",
                  static_cast<unsigned>(capacity), static_cast<unsigned>(trial),
                  static_cast<unsigned>(sizeof(uint64_t) * capacity));
    return;
  }
  const HeapSnapshot after_output_alloc_heap = heapSnapshot();

  t0 = esp_timer_get_time();
  const ssize_t decoded_count = minisketch_decode(source, capacity, decoded);
  const int64_t decode_us = esp_timer_get_time() - t0;
  const HeapSnapshot after_decode_heap = heapSnapshot();
  const bool exact = merged_capacity != 0 && isExpectedDifference(decoded, decoded_count);

  Serial.printf(
      "MSP_RESULT capacity=%u trial=%u exact=%u decoded=%d serialized=%u "
      "receiver_create_us=%lld receiver_build_us=%lld serialize_us=%lld "
      "source_create_us=%lld source_build_us=%lld merge_us=%lld decode_us=%lld "
      "start_free=%u receiver_created_free=%u receiver_built_free=%u "
      "after_receiver_destroy_free=%u before_decode_free=%u output_alloc_free=%u "
      "after_decode_free=%u min_free=%u largest_after_decode=%u\n",
      static_cast<unsigned>(capacity), static_cast<unsigned>(trial), exact ? 1U : 0U,
      static_cast<int>(decoded_count), static_cast<unsigned>(serialized_size),
      static_cast<long long>(receiver_create_us),
      static_cast<long long>(receiver_build_us),
      static_cast<long long>(serialize_us),
      static_cast<long long>(source_create_us),
      static_cast<long long>(source_build_us),
      static_cast<long long>(merge_us),
      static_cast<long long>(decode_us),
      start_heap.free_heap,
      receiver_created_heap.free_heap,
      receiver_built_heap.free_heap,
      after_receiver_destroy.free_heap,
      before_decode_heap.free_heap,
      after_output_alloc_heap.free_heap,
      after_decode_heap.free_heap,
      after_decode_heap.min_free_heap,
      after_decode_heap.largest_block);

  free(decoded);
  minisketch_destroy(remote);
  minisketch_destroy(source);
  free(serialized);

  const HeapSnapshot cleanup_heap = heapSnapshot();
  Serial.printf(
      "MSP_CLEANUP capacity=%u trial=%u free=%u start_free=%u delta=%d\n",
      static_cast<unsigned>(capacity), static_cast<unsigned>(trial),
      cleanup_heap.free_heap, start_heap.free_heap,
      static_cast<int32_t>(cleanup_heap.free_heap) - static_cast<int32_t>(start_heap.free_heap));
}

void runCapacity(size_t capacity) {
  Serial.printf("MSP_CAPACITY_BEGIN capacity=%u trials=%u\n",
                static_cast<unsigned>(capacity), static_cast<unsigned>(TRIALS));
  for (size_t trial = 0; trial < TRIALS; ++trial) {
    runTrial(capacity, trial);
    delay(20);
  }
  Serial.printf("MSP_CAPACITY_END capacity=%u\n", static_cast<unsigned>(capacity));
}
}  // namespace

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.printf(
      "MSP_READY upstream=4a179c61e3cbe3ac2b3c027764ce8eb5183155e1 "
      "bits=16 implementation=0 common=%u unique_each=%u cpu_mhz=%u\n",
      static_cast<unsigned>(COMMON_COUNT), static_cast<unsigned>(UNIQUE_EACH),
      static_cast<unsigned>(ESP.getCpuFreqMHz()));
  printHeap("MSP_BOOT_HEAP", heapSnapshot());

  if (!minisketch_bits_supported(BITS) ||
      !minisketch_implementation_supported(BITS, IMPLEMENTATION)) {
    Serial.println("MSP_FATAL reason=minisketch_16bit_generic_unavailable");
    return;
  }

  // Capacity 20 = upstream fpbits=32 for max_elements=20.
  // Capacity 21 = upstream fpbits=64 for max_elements=20.
  // Capacity 32 = incremental doubling checkpoint / conservative headroom.
  runCapacity(20);
  runCapacity(21);
  runCapacity(32);
  Serial.println("MSP_DONE");
}

void loop() {
  delay(1000);
}
