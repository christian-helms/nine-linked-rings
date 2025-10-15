// bridge.cpp : dynamically linked library supposed to act as a bridge
// between the Manus SDK and an external python script in IsaacLab.

#include "bridge.hpp"
#include "ManusSDKTypes.h"
#include <ManusSDK.h>
#include <cstdint>
#include <iostream>
#include <thread>

#include "ClientLogging.hpp"

extern "C" {
  // C interface for Python ctypes
  Bridge* bridge_create() {
    Bridge* instance = new Bridge();
    ClientReturnCode result = instance->Initialize();
    if (result != ClientReturnCode::ClientReturnCode_Success) {
      delete instance;
      return nullptr;
    }
    return instance;
  }

  int poll(ManusNodePose *buffer, uint32_t buffer_size, uint32_t *count) {
    if (!Bridge::s_Instance) {
      return -1; // Not initialized
    }
    if (!buffer || !count) {
      return -3; // Invalid arguments
    }
    uint32_t actual_count = 0;
    Bridge::s_Instance->Poll(buffer, buffer_size, actual_count);
    *count = actual_count;
    
    // Return -2 if no data is available (count is 0)
    return (actual_count == 0) ? -2 : 0;
  }

  int shutdown() {
    if (!Bridge::s_Instance) {
      return -1; // Not initialized
    }
    ClientReturnCode result = Bridge::s_Instance->ShutDown();
    return (result == ClientReturnCode::ClientReturnCode_Success) ? 0 : -1;
  }
}

using ManusSDK::ClientLog;

Bridge *Bridge::s_Instance = nullptr;

Bridge::Bridge() { s_Instance = this; }

Bridge::~Bridge() { s_Instance = nullptr; }

/// @brief Initialize the sample console and the SDK.
/// This function attempts to resize the console window and then proceeds to
/// initialize the SDK's interface.
ClientReturnCode Bridge::Initialize() {
  if (!PlatformSpecificInitialization()) {
    return ClientReturnCode::
        ClientReturnCode_FailedPlatformSpecificInitialization;
  }

  const ClientReturnCode t_IntializeResult = InitializeSDK();
  if (t_IntializeResult != ClientReturnCode::ClientReturnCode_Success) {
    return ClientReturnCode::ClientReturnCode_FailedToInitialize;
  }

  // first loop until we get a connection
  m_ConnectionType == ConnectionType::ConnectionType_Integrated
      ? ClientLog::print("MANUS Core client is running in integrated mode.")
      : ClientLog::print("MANUS Core client is connecting to MANUS Core. (make "
                         "sure it is running)");

  while (Connect() != ClientReturnCode::ClientReturnCode_Success) {
    // not yet connected. wait
    ClientLog::print(
        "MANUS Core client could not connect.trying again in a second.");
    std::this_thread::sleep_for(std::chrono::milliseconds(1000));
  }

  if (m_ConnectionType != ConnectionType::ConnectionType_Integrated)
    ClientLog::print("MANUS Core client is connected, setting up skeletons.");

  // set the hand motion mode of the RawSkeletonStream. This is optional and can
  // be set to any of the HandMotion enum values. Default = None auto will make
  // it move based on available tracking data. If none is available IMU rotation
  // will be used.
  const SDKReturnCode t_HandMotionResult =
      CoreSdk_SetRawSkeletonHandMotion(HandMotion_Tracker);
  if (t_HandMotionResult != SDKReturnCode::SDKReturnCode_Success) {
    ClientLog::error(
        "Failed to set hand motion mode. The value returned was {}.",
        (int32_t)t_HandMotionResult);
  }
  return ClientReturnCode::ClientReturnCode_Success;
}

/// @brief Initialize the sdk, register the callbacks and set the coordinate
/// system. This needs to be done before any of the other SDK functions can be
/// used.
ClientReturnCode Bridge::InitializeSDK() {
  m_ConnectionType = ConnectionType::ConnectionType_Remote;

  SDKReturnCode t_InitializeResult;
  t_InitializeResult = CoreSdk_InitializeCore();

  if (t_InitializeResult != SDKReturnCode::SDKReturnCode_Success) {
    return ClientReturnCode::ClientReturnCode_FailedToInitialize;
  }

  const ClientReturnCode t_CallBackResults = RegisterAllCallbacks();
  if (t_CallBackResults != ::ClientReturnCode::ClientReturnCode_Success) {
    return t_CallBackResults;
  }

  // after everything is registered and initialized
  // We specify the coordinate system in which we want to receive the data.
  // (each client can have their own settings. unreal and unity for instance use
  // different coordinate systems) if this is not set, the SDK will not
  // function. The coordinate system used for this example is z-up, x-positive,
  // right-handed and in meter scale.
  CoordinateSystemVUH t_VUH;
  CoordinateSystemVUH_Init(&t_VUH);
  t_VUH.handedness = Side::Side_Right;
  t_VUH.up = AxisPolarity::AxisPolarity_PositiveZ;
  t_VUH.view = AxisView::AxisView_XFromViewer;
  t_VUH.unitScale = 1.0f; // 1.0 is meters, 0.01 is cm, 0.001 is mm.

  // The above specified coordinate system is used to initialize and the
  // coordinate space is specified (world vs local).
  const SDKReturnCode t_CoordinateResult =
      CoreSdk_InitializeCoordinateSystemWithVUH(t_VUH, true);

  if (t_CoordinateResult != SDKReturnCode::SDKReturnCode_Success) {
    return ClientReturnCode::ClientReturnCode_FailedToInitialize;
  }

  return ClientReturnCode::ClientReturnCode_Success;
}

/// @brief When shutting down the application, it's important to clean up after
/// the SDK and call it's shutdown function. this will close all connections to
/// the host, close any threads. after this is called it is expected to exit the
/// client program. If not you would need to reinitalize the SDK.
ClientReturnCode Bridge::ShutDown() {
  const SDKReturnCode t_Result = CoreSdk_ShutDown();
  if (t_Result != SDKReturnCode::SDKReturnCode_Success) {
    return ClientReturnCode::ClientReturnCode_FailedToShutDownSDK;
  }

  if (!PlatformSpecificShutdown()) {
    return ClientReturnCode::ClientReturnCode_FailedPlatformSpecificShutdown;
  }

  return ClientReturnCode::ClientReturnCode_Success;
}

/// @brief Used to register all the stream callbacks.
/// Callbacks that are registered functions that get called when a certain
/// 'event' happens, such as data coming in. All of these are optional, but
/// depending on what data you require you may or may not need all of them. For
/// this example we only implement the raw skeleton data.
ClientReturnCode Bridge::RegisterAllCallbacks() {
  // Register the callback to receive Raw Skeleton data
  // it is optional, but without it you can not see any resulting skeleton data.
  // see OnRawSkeletonStreamCallback for more details.
  const SDKReturnCode t_RegisterRawSkeletonCallbackResult =
      CoreSdk_RegisterCallbackForRawSkeletonStream(
          *OnRawSkeletonStreamCallback);
  if (t_RegisterRawSkeletonCallbackResult !=
      SDKReturnCode::SDKReturnCode_Success) {
    ClientLog::error(
        "Failed to register callback function for processing raw skeletal data "
        "from Manus Core. The value returned was {}.",
        (int32_t)t_RegisterRawSkeletonCallbackResult);
    return ClientReturnCode::ClientReturnCode_FailedToInitialize;
  }

  return ClientReturnCode::ClientReturnCode_Success;
}

/// @brief Poll for the latest skeleton data and write it to the provided buffer.
/// This function retrieves the most recent skeleton data from the SDK callback
/// and formats it into a flat array of ManusNodePose structures. The function
/// is thread-safe and will swap the latest data from the callback thread.
/// @param buffer Pointer to the output buffer for node poses
/// @param buffer_size Maximum number of nodes the buffer can hold
/// @param count Output parameter set to the number of nodes written to the buffer
void Bridge::Poll(ManusNodePose *buffer, uint32_t buffer_size,
                  uint32_t &count) {
  m_RawSkeletonMutex.lock();

  // Swap in the latest skeleton data from the callback thread
  delete m_RawSkeleton;
  m_RawSkeleton = m_NextRawSkeleton;
  m_NextRawSkeleton = nullptr;

  count = 0; // Initialize count to zero
  
  // Check if we have valid skeleton data
  if (!m_RawSkeleton || m_RawSkeleton->skeletons.size() == 0) {
    m_RawSkeletonMutex.unlock();
    return; // No data available yet
  }

  uint32_t t_SkeletonCount = m_RawSkeleton->skeletons.size();
  uint32_t buffer_index = 0;

  for (uint32_t i = 0; i < t_SkeletonCount; i++) {
    uint32_t t_GloveId = m_RawSkeleton->skeletons[i].info.gloveId;
    uint32_t t_NodeCount = m_RawSkeleton->skeletons[i].info.nodesCount;
    
    // Check if we have enough buffer space
    if (buffer_index + t_NodeCount > buffer_size) {
      ClientLog::error("Buffer overflow prevented: need {} slots but only {} available",
                       buffer_index + t_NodeCount, buffer_size);
      break;
    }
    
    NodeInfo node_info[t_NodeCount];
    SDKReturnCode result = CoreSdk_GetRawSkeletonNodeInfoArray(t_GloveId, node_info, t_NodeCount);
    if (result != SDKReturnCode::SDKReturnCode_Success) {
      ClientLog::error("Failed to get node info array for glove {}", t_GloveId);
      continue;
    }

    for (uint32_t j = 0; j < t_NodeCount; j++) {
      const SkeletonNode& node = m_RawSkeleton->skeletons[i].nodes[j];
      ManusNodePose &node_pose = buffer[buffer_index++];
      node_pose.glove_id = t_GloveId;
      node_pose.node_id = node_info[j].nodeId;
      node_pose.side = node_info[j].side;
      node_pose.position = node.transform.position;
      node_pose.orientation = node.transform.rotation;
    }
  }
  
  count = buffer_index; // Set the actual number of nodes written

  m_RawSkeletonMutex.unlock();
}


/// @brief the client will now try to connect to MANUS Core via the SDK when the
/// ConnectionType is not integrated. These steps still need to be followed when
/// using the integrated ConnectionType.
ClientReturnCode Bridge::Connect() {
  bool t_ConnectLocally =
      m_ConnectionType == ConnectionType::ConnectionType_Local;
  SDKReturnCode t_StartResult = CoreSdk_LookForHosts(1, t_ConnectLocally);
  if (t_StartResult != SDKReturnCode::SDKReturnCode_Success) {
    return ClientReturnCode::ClientReturnCode_FailedToFindHosts;
  }

  uint32_t t_NumberOfHostsFound = 0;
  SDKReturnCode t_NumberResult =
      CoreSdk_GetNumberOfAvailableHostsFound(&t_NumberOfHostsFound);
  if (t_NumberResult != SDKReturnCode::SDKReturnCode_Success) {
    return ClientReturnCode::ClientReturnCode_FailedToFindHosts;
  }

  if (t_NumberOfHostsFound == 0) {
    return ClientReturnCode::ClientReturnCode_FailedToFindHosts;
  }

  std::unique_ptr<ManusHost[]> t_AvailableHosts;
  t_AvailableHosts.reset(new ManusHost[t_NumberOfHostsFound]);

  SDKReturnCode t_HostsResult = CoreSdk_GetAvailableHostsFound(
      t_AvailableHosts.get(), t_NumberOfHostsFound);
  if (t_HostsResult != SDKReturnCode::SDKReturnCode_Success) {
    return ClientReturnCode::ClientReturnCode_FailedToFindHosts;
  }

  uint32_t t_HostSelection = 0;
  if (!t_ConnectLocally && t_NumberOfHostsFound > 1) {
    ClientLog::print(
        "Select which host you want to connect to (and press enter to submit)");
    for (size_t i = 0; i < t_NumberOfHostsFound; i++) {
      auto t_HostInfo = t_AvailableHosts[i];
      ClientLog::print("[{}] hostname: {} IP address: {}, version {}.{}.{}",
                       i + 1, t_HostInfo.hostName, t_HostInfo.ipAddress,
                       t_HostInfo.manusCoreVersion.major,
                       t_HostInfo.manusCoreVersion.minor,
                       t_HostInfo.manusCoreVersion.patch);
    }
    uint32_t t_HostSelectionInput = 0;
    std::cin >> t_HostSelectionInput;
    if (t_HostSelectionInput <= 0 ||
        t_HostSelectionInput > t_NumberOfHostsFound)
      return ClientReturnCode::ClientReturnCode_FailedToConnect;

    t_HostSelection = t_HostSelectionInput - 1;
  }

  SDKReturnCode t_ConnectResult =
      CoreSdk_ConnectToHost(t_AvailableHosts[t_HostSelection]);

  if (t_ConnectResult == SDKReturnCode::SDKReturnCode_NotConnected) {
    return ClientReturnCode::ClientReturnCode_FailedToConnect;
  }

  return ClientReturnCode::ClientReturnCode_Success;
}

/// @brief This gets called when the client is connected and there is glove data
/// available.
/// @param p_RawSkeletonStreamInfo contains the meta data on what data is
/// available and needs to be retrieved from the SDK. The data is not directly
/// passed to the callback, but needs to be retrieved from the SDK for it to be
/// used. This is demonstrated in the function below.
void Bridge::OnRawSkeletonStreamCallback(
    const SkeletonStreamInfo *const p_RawSkeletonStreamInfo) {
  if (s_Instance) {
    ClientRawSkeletonCollection *t_NxtClientRawSkeleton =
        new ClientRawSkeletonCollection();
    t_NxtClientRawSkeleton->skeletons.resize(
        p_RawSkeletonStreamInfo->skeletonsCount);

    for (uint32_t i = 0; i < p_RawSkeletonStreamInfo->skeletonsCount; i++) {
      // Retrieves info on the skeletonData, like deviceID and the amount of
      // nodes.
      CoreSdk_GetRawSkeletonInfo(i, &t_NxtClientRawSkeleton->skeletons[i].info);
      t_NxtClientRawSkeleton->skeletons[i].nodes.resize(
          t_NxtClientRawSkeleton->skeletons[i].info.nodesCount);
      t_NxtClientRawSkeleton->skeletons[i].info.publishTime =
          p_RawSkeletonStreamInfo->publishTime;

      // Retrieves the skeletonData, which contains the node data.
      CoreSdk_GetRawSkeletonData(
          i, t_NxtClientRawSkeleton->skeletons[i].nodes.data(),
          t_NxtClientRawSkeleton->skeletons[i].info.nodesCount);
    }
    s_Instance->m_RawSkeletonMutex.lock();
    if (s_Instance->m_NextRawSkeleton != nullptr)
      delete s_Instance->m_NextRawSkeleton;
    s_Instance->m_NextRawSkeleton = t_NxtClientRawSkeleton;
    s_Instance->m_RawSkeletonMutex.unlock();
  }
}
