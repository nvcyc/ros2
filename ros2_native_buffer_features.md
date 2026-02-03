# ROS2 Native Buffer Feature

## Overview

The Native Buffer feature introduces a zero-copy memory management system to ROS2, enabling efficient data transfer between publishers and subscribers that may use different memory backends (CPU, GPU, custom accelerators). This feature is particularly valuable for robotics applications involving large data payloads such as images, point clouds, and sensor data where memory copies are a significant performance bottleneck.

## Motivation

Traditional ROS2 message passing involves multiple memory copies:
1. Application writes to message fields
2. Serialization copies data to a wire format
3. Transport layer may copy data again
4. Deserialization copies data to subscriber's message

For large messages (images, point clouds, LiDAR scans), these copies can consume significant CPU time and memory bandwidth, limiting real-time performance.

The Native Buffer feature addresses this by:
- Providing a unified `Buffer<T>` type that can wrap data from any memory backend
- Enabling endpoint-aware serialization that adapts based on publisher/subscriber capabilities
- Supporting zero-copy transfers when publisher and subscriber share compatible memory backends
- Maintaining full backward compatibility with existing ROS2 code

## Scope

**Important**: The `Buffer<T>` type is specifically designed to replace **only `uint8[]` (unbounded byte array) fields**, not all array types in ROS2 messages.

### Why Only uint8[]?

1. **Target Use Case**: The primary use case is large binary data blobs like:
   - Image pixel data (`sensor_msgs/Image.data`)
   - Point cloud data (`sensor_msgs/PointCloud2.data`)
   - Compressed data streams
   - Raw sensor buffers

2. **Semantic Meaning**: `uint8[]` fields typically represent raw byte buffers where:
   - The data is opaque binary content
   - The size is large and variable
   - Zero-copy optimization provides significant benefit

3. **Other Array Types Unchanged**: Arrays of other types remain as `std::vector<T>`:
   - `float32[]` stays as `std::vector<float>`
   - `int32[]` stays as `std::vector<int32_t>`
   - Bounded arrays `uint8[N]` stay as `std::array<uint8_t, N>`
   - These typically have semantic meaning where each element matters individually

### Field Detection

The code generator identifies `uint8[]` fields by checking:
```python
# In rosidl_generator_cpp
if member.type.typename == 'uint8' and isinstance(member.type, AbstractNestedType):
    if isinstance(member.type, UnboundedSequence):
        # This field becomes Buffer<uint8_t>
```

## Key Features

### 1. Buffer<uint8_t> Type
A new container type that replaces `uint8[]` (unbounded byte sequence) fields in generated message types:

```cpp
// Before (uint8[] data in .msg file):
std::vector<uint8_t> data;

// After (uint8[] data in .msg file):
rosidl_runtime_cpp::Buffer<uint8_t> data;

// Other array types remain unchanged:
std::vector<float> floats;        // float32[] floats
std::vector<int32_t> integers;    // int32[] integers
std::array<uint8_t, 16> fixed;    // uint8[16] fixed
```

The `Buffer<uint8_t>` type provides:
- Transparent access to underlying data via iterators and index operators
- Automatic memory management with reference counting
- Support for multiple memory backends (CPU, GPU, custom)
- Implicit conversion from `std::vector<uint8_t>` for backward compatibility

### 2. Endpoint-Aware Serialization
Publishers can serialize data differently based on the subscriber's capabilities:
- If subscriber supports the same memory backend, data can be transferred by reference
- If subscriber uses a different backend, data is serialized normally
- Enables optimal data transfer paths without application code changes

### 3. Backend Plugin System
A pluggable architecture for memory backends:
- **CPU Backend**: Standard heap-allocated memory (default)
- **GPU Backend**: CUDA/device memory for GPU-accelerated pipelines
- **Custom Backends**: Extensible for specialized hardware (FPGAs, NPUs, etc.)

### 4. Discovery-Based Optimization
Publishers and subscribers exchange backend capability information during discovery:
- Backend types and auxiliary information are included in liveliness tokens
- RMW layer creates optimized communication paths based on matched capabilities
- Automatic fallback to standard serialization when backends are incompatible

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Application Layer                            │
│  ┌─────────────┐                           ┌─────────────┐      │
│  │  Publisher  │                           │ Subscriber  │      │
│  │             │                           │             │      │
│  │ Buffer<T>   │                           │ Buffer<T>   │      │
│  └──────┬──────┘                           └──────┬──────┘      │
└─────────┼───────────────────────────────────────────┼───────────┘
          │                                           │
┌─────────┼───────────────────────────────────────────┼───────────┐
│         │        Type Support Layer                 │           │
│  ┌──────▼──────┐                           ┌───────▼──────┐     │
│  │ Endpoint-   │                           │ Endpoint-    │     │
│  │ Aware       │                           │ Aware        │     │
│  │ Serialize   │                           │ Deserialize  │     │
│  └──────┬──────┘                           └───────┬──────┘     │
└─────────┼───────────────────────────────────────────┼───────────┘
          │                                           │
┌─────────┼───────────────────────────────────────────┼───────────┐
│         │           RMW Layer (rmw_zenoh)           │           │
│  ┌──────▼──────┐    Discovery    ┌─────────────────▼──────┐    │
│  │ Publisher   │◄───Callbacks───►│ Subscription           │    │
│  │ Data        │                 │ Data                   │    │
│  │             │                 │                        │    │
│  │ Backend     │                 │ Backend                │    │
│  │ Aux Info    │                 │ Aux Info               │    │
│  └──────┬──────┘                 └─────────────────┬──────┘    │
└─────────┼───────────────────────────────────────────┼───────────┘
          │                                           │
┌─────────┼───────────────────────────────────────────┼───────────┐
│         │      Buffer Backend Registry              │           │
│  ┌──────▼──────────────────────────────────────────▼──────┐    │
│  │                  Backend Plugins                        │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │    │
│  │  │   CPU   │  │   GPU   │  │  FPGA   │  │ Custom  │   │    │
│  │  │ Backend │  │ Backend │  │ Backend │  │ Backend │   │    │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Package Changes

### rosidl_runtime_cpp
New headers added:
- `buffer.hpp` - Core `Buffer<T>` template class
- `buffer__traits.hpp` - Type traits for Buffer detection
- `buffer_impl_base.hpp` - Abstract base class for buffer implementations
- `cpu_buffer_impl.hpp` - Default CPU memory backend implementation

### rosidl_generator_cpp
Modified to generate `Buffer<uint8_t>` instead of `std::vector<uint8_t>` for `uint8[]` fields:
- `__init__.py` - Added `has_buffer_fields` detection logic (checks for `uint8[]` fields)
- `idl__struct.hpp.em` - Template changes for Buffer types
- `idl__traits.hpp.em` - Added Buffer type traits

### rosidl_typesupport_fastrtps_cpp
Added endpoint-aware serialization support:
- `buffer_serialization.hpp` - Serialization helpers for Buffer types
- `message_type_support.h` - New callback signatures for endpoint-aware serialize/deserialize
- `msg__type_support.cpp.em` - Added `has_buffer_fields` member to type support
- `idl__type_support.cpp.em` - Endpoint-aware serialization function generation

### rosidl_buffer_registry (New Package)
Plugin system for memory backends:
- `buffer_registry.hpp` - Backend interface definitions
- `buffer_registry.cpp` - Plugin loading and registration

### rmw_zenoh_cpp
RMW layer integration:
- `buffer_backend_loader.hpp/cpp` - Backend discovery and compatibility checking
- `liveliness_utils.hpp/cpp` - Extended TopicInfo with backend aux info
- `graph_cache.hpp/cpp` - Discovery callbacks for pub/sub matching
- `rmw_publisher_data.hpp/cpp` - Buffer-aware publishing logic
- `rmw_subscription_data.hpp/cpp` - Buffer-aware subscription logic
- `rmw_context_impl_s.cpp` - Backend lifecycle management

## API Reference

### Buffer<T> Class

The `Buffer<T>` is a template class, but **only `Buffer<uint8_t>` is used in generated message code** (for `uint8[]` fields). The template design allows for potential future expansion.

```cpp
namespace rosidl_runtime_cpp {

template<typename T>
class Buffer {
public:
  // Construction
  Buffer();                                    // Empty buffer
  Buffer(std::vector<T> && data);             // Move from vector
  Buffer(const std::vector<T> & data);        // Copy from vector
  Buffer(std::shared_ptr<BufferImplBase<T>>); // From backend implementation
  
  // Element access
  T & operator[](size_t index);
  const T & operator[](size_t index) const;
  T * data();
  const T * data() const;
  
  // Capacity
  size_t size() const;
  bool empty() const;
  void resize(size_t new_size);
  void reserve(size_t new_capacity);
  
  // Iterators
  iterator begin();
  iterator end();
  const_iterator begin() const;
  const_iterator end() const;
  
  // Modifiers
  void push_back(const T & value);
  void push_back(T && value);
  void clear();
  
  // Backend access
  std::shared_ptr<BufferImplBase<T>> get_impl() const;
  std::string backend_type() const;
  
  // Conversion
  operator std::vector<T>() const;  // Implicit conversion to vector
};

// Primary instantiation used in generated messages:
using ByteBuffer = Buffer<uint8_t>;

} // namespace rosidl_runtime_cpp
```

### Backend Plugin Interface

```cpp
namespace rosidl_buffer_registry {

class BufferBackend {
public:
  virtual ~BufferBackend() = default;
  
  // Backend identification
  virtual std::string type_name() const = 0;
  virtual std::string get_aux_info() const = 0;
  
  // Lifecycle callbacks
  virtual void on_creating_endpoint(
    const rmw_topic_endpoint_info_t & endpoint_info) = 0;
    
  virtual std::unordered_map<std::string, bool> on_discovering_endpoint(
    const rmw_topic_endpoint_info_t & discovered_endpoint,
    const std::vector<rmw_topic_endpoint_info_t> & existing_endpoints,
    const std::unordered_map<std::string, std::string> & remote_aux_info) = 0;
};

// Plugin registration
void register_backend(std::shared_ptr<BufferBackend> backend);
std::vector<std::string> get_installed_backend_types();

} // namespace rosidl_buffer_registry
```

## Usage Examples

### Affected Message Types

Common ROS2 messages with `uint8[]` fields that benefit from this feature:

| Message Type | Field | Description |
|-------------|-------|-------------|
| `sensor_msgs/Image` | `data` | Raw image pixel data |
| `sensor_msgs/PointCloud2` | `data` | Point cloud binary data |
| `sensor_msgs/CompressedImage` | `data` | Compressed image bytes |
| `sensor_msgs/LaserScan` | (none) | Uses `float32[]`, not affected |
| `geometry_msgs/Pose` | (none) | No array fields, not affected |

### Basic Usage (Transparent)

Existing code continues to work without modification. The `data` field (previously `std::vector<uint8_t>`) is now `Buffer<uint8_t>`, but the API is compatible:

```cpp
// Publisher - sensor_msgs::msg::Image::data is now Buffer<uint8_t>
auto msg = std::make_unique<sensor_msgs::msg::Image>();
msg->data.resize(width * height * 3);  // Works the same as before
// Fill data...
publisher->publish(std::move(msg));

// Subscriber
void callback(const sensor_msgs::msg::Image::SharedPtr msg) {
  // Access data normally - Buffer<uint8_t> has same interface as vector
  for (size_t i = 0; i < msg->data.size(); ++i) {
    process(msg->data[i]);
  }
}
```

### Explicit Buffer Usage

For advanced use cases with custom backends:

```cpp
#include "rosidl_runtime_cpp/buffer.hpp"
#include "rosidl_runtime_cpp/cpu_buffer_impl.hpp"

// Create a buffer with specific backend
auto impl = std::make_shared<rosidl_runtime_cpp::CpuBufferImpl<uint8_t>>();
impl->resize(1024);
rosidl_runtime_cpp::Buffer<uint8_t> buffer(impl);

// Use in message
auto msg = std::make_unique<sensor_msgs::msg::Image>();
msg->data = std::move(buffer);
publisher->publish(std::move(msg));
```

### Custom Backend Plugin

```cpp
#include "rosidl_buffer_registry/buffer_registry.hpp"

class MyGpuBackend : public rosidl_buffer_registry::BufferBackend {
public:
  std::string type_name() const override { return "my_gpu"; }
  
  std::string get_aux_info() const override {
    return "device_id=0;cuda_version=12.0";
  }
  
  void on_creating_endpoint(
    const rmw_topic_endpoint_info_t & endpoint_info) override {
    // Initialize GPU resources for this endpoint
  }
  
  std::unordered_map<std::string, bool> on_discovering_endpoint(
    const rmw_topic_endpoint_info_t & discovered_endpoint,
    const std::vector<rmw_topic_endpoint_info_t> & existing_endpoints,
    const std::unordered_map<std::string, std::string> & remote_aux_info) override {
    // Check if remote endpoint supports GPU backend
    std::unordered_map<std::string, bool> compat;
    compat["my_gpu"] = remote_aux_info.count("my_gpu") > 0;
    return compat;
  }
};

// Register during plugin initialization
ROSIDL_BUFFER_REGISTRY_REGISTER_BACKEND(MyGpuBackend)
```

## Backward Compatibility

The Native Buffer feature maintains full backward compatibility:

1. **Source Compatibility**: Existing code compiles without changes
   - `Buffer<T>` provides implicit conversion to/from `std::vector<T>`
   - Standard iterator and index-based access work identically

2. **Binary Compatibility**: Wire format remains unchanged
   - Standard CDR serialization for cross-RMW communication
   - Optimized paths only used when both endpoints support them

3. **Behavioral Compatibility**: Existing behavior preserved
   - Messages without Buffer fields use standard serialization
   - Backend discovery is opt-in via `has_buffer_fields` flag

## Performance Considerations

### When Zero-Copy Applies
- Same process, same memory backend
- Shared memory transport with compatible backends
- GPU-to-GPU transfers with matching CUDA contexts

### When Standard Serialization is Used
- Different memory backends without compatibility
- Network transport between machines
- Mixed RMW implementations

### Memory Overhead
- `Buffer<T>` has slightly larger memory footprint than `std::vector<T>` due to backend metadata
- Reference counting enables safe zero-copy without explicit lifetime management

## Future Work

1. **Additional Backends**
   - CUDA GPU backend
   - Vulkan compute backend
   - FPGA memory backend

2. **Transport Optimizations**
   - Shared memory zero-copy for local communication
   - RDMA support for high-performance networking

3. **Tooling**
   - `ros2 topic info` extended to show backend capabilities
   - Performance profiling tools for Buffer transfers

## Contributing

This feature is developed as part of the ROS2 Rolling distribution. Contributions are welcome:

1. Review the implementation in the packages listed above
2. Test with your use cases and report issues
3. Implement additional backend plugins
4. Improve documentation and examples

## References

- [ROS2 Design: Zero Copy](https://design.ros2.org/articles/zero_copy.html)
- [DDS-XTYPES Specification](https://www.omg.org/spec/DDS-XTypes/)
- [Zenoh Protocol](https://zenoh.io/)
