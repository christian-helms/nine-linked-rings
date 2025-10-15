#ifndef _SDK_MINIMAL_CLIENT_HPP_
#define _SDK_MINIMAL_CLIENT_HPP_

#include "ClientPlatformSpecific.hpp"
#include "ManusSDK.h"
#include <mutex>
#include <vector>

/// @brief The type of connection to core.
enum class ConnectionType : int {
  ConnectionType_Invalid = 0,
  ConnectionType_Integrated,
  ConnectionType_Local,
  ConnectionType_Remote,
  ClientState_MAX_CLIENT_STATE_SIZE
};

/// @brief Values that can be returned by this application.
enum class ClientReturnCode : int {
  ClientReturnCode_Success = 0,
  ClientReturnCode_FailedPlatformSpecificInitialization,
  ClientReturnCode_FailedToResizeWindow,
  ClientReturnCode_FailedToInitialize,
  ClientReturnCode_FailedToFindHosts,
  ClientReturnCode_FailedToConnect,
  ClientReturnCode_UnrecognizedStateEncountered,
  ClientReturnCode_FailedToShutDownSDK,
  ClientReturnCode_FailedPlatformSpecificShutdown,
  ClientReturnCode_FailedToRestart,
  ClientReturnCode_FailedWrongTimeToGetData,

  ClientReturnCode_MAX_CLIENT_RETURN_CODE_SIZE
};

/// @brief Represents a single node (joint) pose for a Manus glove.
/// This struct uses C-compatible layout for Python ctypes interoperability.
struct ManusNodePose {
  uint32_t glove_id;
  uint32_t node_id;
  uint32_t side;
  ManusVec3 position;
  ManusQuaternion orientation;
};

// C interface for Python ctypes
#ifdef __cplusplus
extern "C" {
#endif

class Bridge;

Bridge* bridge_create();
int poll(ManusNodePose *buffer, uint32_t buffer_size, uint32_t *count);
int shutdown();

#ifdef __cplusplus
}
#endif

/// @brief Used to store the information about the skeleton data coming from the
/// estimation system in Core.
class ClientRawSkeleton {
public:
  RawSkeletonInfo info;
  std::vector<SkeletonNode> nodes;
};

/// @brief Used to store all the skeleton data coming from the estimation system
/// in Core.
class ClientRawSkeletonCollection {
public:
  std::vector<ClientRawSkeleton> skeletons;
};

class Bridge : public SDKClientPlatformSpecific {
public:
  static Bridge *s_Instance;

  Bridge();
  ~Bridge();
  ClientReturnCode Initialize();
  ClientReturnCode InitializeSDK();
  ClientReturnCode RegisterAllCallbacks();
  ClientReturnCode ShutDown();
  void Poll(ManusNodePose *buffer, uint32_t buffer_size, uint32_t &count);

  void PrintRawSkeletonNodeInfo();

  static void OnRawSkeletonStreamCallback(
      const SkeletonStreamInfo *const p_RawSkeletonStreamInfo);

protected:
  ClientReturnCode Connect();

  bool m_PrintedNodeInfo = false;

  ConnectionType m_ConnectionType = ConnectionType::ConnectionType_Remote;

  std::mutex m_RawSkeletonMutex;
  ClientRawSkeletonCollection *m_NextRawSkeleton = nullptr;
  ClientRawSkeletonCollection *m_RawSkeleton = nullptr;

  uint32_t m_FrameCounter = 0;
};
#endif
