**********************
Inizio trascrizione Windows PowerShell
Ora di inizio: 20260323161435
Nome utente: PCDOTT-PIERESSA\andrea
Esegui come utente: PCDOTT-PIERESSA\andrea
Nome configurazione: 
Computer PCDOTT-PIERESSA (Microsoft Windows NT 10.0.26200.0)
Applicazione host: C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
ID processo: 28152
PSVersion: 5.1.26100.7920
PSEdition: Desktop
PSCompatibleVersions: 1.0, 2.0, 3.0, 4.0, 5.0, 5.1.26100.7920
BuildVersion: 10.0.26100.7920
CLRVersion: 4.0.30319.42000
WSManStackVersion: 3.0
PSRemotingProtocolVersion: 2.3
SerializationVersion: 1.1.0.1
**********************
Trascrizione avviata. File di output: .\docs\interactive_session.md
PS C:\Users\andrea\projects\baumer_vcxg232c_test>
(.venv) python -m src.main --interactive
DEBUG: Starting main with args: ['--interactive']
Connecting to camera 'any'...

Interactive session error: Failed to connect to camera: NotConnectedException: No device with '' found.
Traceback (most recent call last):
  File "C:\Users\andrea\projects\baumer_vcxg232c_test\src\camera_test.py", line 429, in _connect_camera
    cam.Connect()
  File "C:\Users\andrea\projects\baumer_vcxg232c_test\.venv\lib\site-packages\neoapi\neoapi.py", line 19702, in Connect
    return _neoapi.Cam_Connect(self, *args)
neoapi.neoapi.NotConnectedException: NotConnectedException: No device with '' found.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\andrea\projects\baumer_vcxg232c_test\src\camera_test.py", line 241, in run_interactive_mode
    _connect_camera(cam, config.camera_id)
  File "C:\Users\andrea\projects\baumer_vcxg232c_test\src\camera_test.py", line 432, in _connect_camera
    raise CameraTestError(f"Failed to connect to camera{target}: {exc}") from exc
src.camera_test.CameraTestError: Failed to connect to camera: NotConnectedException: No device with '' found.
Camera disconnected.
PS C:\Users\andrea\projects\baumer_vcxg232c_test>
(.venv) PS C:\Users\andrea\projects\baumer_vcxg232c_test> python -m src.main --interactive
DEBUG: Starting main with args: ['--interactive']
Connecting to camera 'any'...

Connected to: VCXG.2-32C (700013703394) at 172.31.1.200
Interactive mode active. Type 'help' for commands.

camera> ls
Feature Name                             | Interface       | Value
--------------------------------------------------------------------------------
DeviceTemperatureStatusTransition        | IInteger        | 67
DeviceLinkSelector                       | IInteger        | 0
DeviceFirmwareVersion                    | IString         | CID:014003/PID:11707066
ReadOutTime                              | IInteger        | 17801
GevCurrentIPConfigurationLLA             | IBoolean        | 1
CustomData                               | IInteger        | 0xff
DeviceTLVersionMinor                     | IInteger        | 0
AcquisitionStatus                        | IBoolean        | 1
AcquisitionAbort                         | ICommand        | [Not Readable]
AcquisitionStart                         | ICommand        | [Not Readable]
AcquisitionFrameCount                    | IInteger        | 1
CustomDataSelector                       | IInteger        | 0
ChunkModeActive                          | IBoolean        | 0
TestPatternGeneratorSelector             | IEnumeration    | ImageProcessor
AcquisitionStatusSelector                | IEnumeration    | AcquisitionActive
SensorPixelWidth                         | IFloat          | 3.45
AcquisitionFrameRate                     | IFloat          | 10
PayloadSize                              | IInteger        | 3145728
ActionDeviceKey                          | IInteger        | [Not Readable]
AcquisitionFrameRateEnable               | IBoolean        | 0
DeviceEventChannelCount                  | IInteger        | 1
ExposureAuto                             | IEnumeration    | Continuous
ChunkSelector                            | IEnumeration    | Image
LostEventCounter                         | IInteger        | 0
GevPAUSEFrameReception                   | IBoolean        | 1
AcquisitionMode                          | IEnumeration    | Continuous
AcquisitionStop                          | ICommand        | [Not Readable]
ActionGroupKey                           | IInteger        | 0x0
DefectPixelListEntryPosX                 | IInteger        | 9
TriggerOverlap                           | IEnumeration    | ReadOut
ActionGroupMask                          | IInteger        | 0x0
GevPrimaryApplicationSwitchoverKey       | IInteger        | [Not Readable]
ActionSelector                           | IInteger        | 1
AutoFeatureHeight                        | IInteger        | 1536
DefectPixelListSelector                  | IEnumeration    | Pixel
AutoFeatureOffsetX                       | IInteger        | 0
GevMCRC                                  | IInteger        | 2
AutoFeatureOffsetY                       | IInteger        | 0
BlackLevelSelector                       | IEnumeration    | All
AutoFeatureRegionMode                    | IEnumeration    | Off
ChunkEnable                              | IBoolean        | 0
UserSetFeatureSelector                   | IEnumeration    | AcquisitionFrameCount
AutoFeatureRegionReference               | IEnumeration    | Region0
ColorTransformationResetToFactoryList    | ICommand        | Done
AutoFeatureRegionSelector                | IEnumeration    | BrightnessAuto
DeviceSFNCVersionMajor                   | IInteger        | 2
AutoFeatureWidth                         | IInteger        | 2048
UserOutputValueAll                       | IInteger        | 0
BalanceWhiteAuto                         | IEnumeration    | Continuous
BalanceWhiteAutoStatus                   | IEnumeration    | Start
BinningHorizontal                        | IInteger        | 1
ColorTransformationOutputColorSpace      | IString         | sRGB Gamma 1
DeviceIndicatorMode                      | IEnumeration    | Active
GainSelector                             | IEnumeration    | All
ColorTransformationValueSelector         | IEnumeration    | Gain00
BinningHorizontalMode                    | IEnumeration    | Sum
BinningSelector                          | IEnumeration    | Region0
BinningVertical                          | IInteger        | 1
DefectPixelListEntryPosY                 | IInteger        | 1113
BinningVerticalMode                      | IEnumeration    | Sum
BlackLevel                               | IFloat          | 0
ColorTransformationEnable                | IBoolean        | 0
DefectPixelListEntryActive               | IBoolean        | 1
CounterValue                             | IInteger        | 0
CounterValueAtReset                      | IInteger        | 0
BrightnessAutoNominalValue               | IFloat          | 50
OffsetY                                  | IInteger        | 0
BrightnessAutoPriority                   | IEnumeration    | ExposureAuto
ColorTransformationAuto                  | IEnumeration    | Off
CounterEventSource                       | IEnumeration    | Off
ColorTransformationFactoryListSelector   | IEnumeration    | OptimizedMatrixFor6500K
boCalibrationDataVersion                 | IString         | 1.0
Gain                                     | IFloat          | 1
ColorTransformationValue                 | IFloat          | 1.23828
CounterDuration                          | IInteger        | 1
CounterEventActivation                   | IEnumeration    | RisingEdge
DeviceCharacterSet                       | IEnumeration    | UTF8
CounterReset                             | ICommand        | Done
CounterSelector                          | IEnumeration    | Counter1
CounterResetActivation                   | IEnumeration    | RisingEdge
boGeometryDistortionValueSelector        | IEnumeration    | k1
CounterResetSource                       | IEnumeration    | Off
CustomDataConfigurationMode              | IEnumeration    | Off
DefectPixelCorrection                    | IBoolean        | 1
boCalibrationVectorSelector              | IEnumeration    | tvec
DeviceFamilyName                         | IString         | VCXG
DefectPixelListIndex                     | IInteger        | 0
GevSCPD                                  | IInteger        | 0
DeviceLinkCommandTimeout                 | IFloat          | 200000
DeviceLinkHeartbeatMode                  | IEnumeration    | On
DeviceLinkHeartbeatTimeout               | IFloat          | 3e+06
DeviceLinkSpeed                          | IInteger        | 125000000
DeviceLinkThroughputLimit                | IInteger        | 125000000
DeviceManufacturerInfo                   | IString         | F:04012A23/C:04012A17/BL3.8:04012A0D
DeviceModelName                          | IString         | VCXG.2-32C
LineDebouncerLowTimeAbs                  | IFloat          | 0
GevPersistentIPAddress                   | IInteger        | 172.31.1.200
GevCurrentIPConfigurationPersistentIP    | IBoolean        | 1
DeviceRegistersEndianness                | IEnumeration    | Big
DeviceReset                              | ICommand        | [Not Readable]
DeviceResetToDeliveryState               | ICommand        | [Not Readable]
DeviceSFNCVersionMinor                   | IInteger        | 4
DeviceSFNCVersionSubMinor                | IInteger        | 0
DeviceScanType                           | IEnumeration    | Areascan
DeviceSensorType                         | IEnumeration    | CMOS
MemoryMaxBlocks                          | IInteger        | 8
DeviceSerialNumber                       | IString         | 700013703394
ImageDataEnable                          | IBoolean        | 0
DeviceStreamChannelCount                 | IInteger        | 1
DeviceStreamChannelEndianness            | IEnumeration    | Little
DeviceTLType                             | IEnumeration    | GigEVision
DeviceStreamChannelPacketSize            | IInteger        | 9000
DeviceStreamChannelSelector              | IInteger        | 0
DeviceStreamChannelType                  | IEnumeration    | Transmitter
DeviceTLVersionMajor                     | IInteger        | 2
DeviceTLVersionSubMinor                  | IInteger        | 0
GevSCPSPacketSize                        | IInteger        | 9000
DeviceTemperature                        | IFloat          | 44.6875
DeviceTemperatureExceeded                | IBoolean        | 0
boCalibrationVectorValue                 | IFloat          | 0
DeviceTemperatureSelector                | IEnumeration    | InHouse
DeviceTemperatureStatus                  | IEnumeration    | Normal
DeviceTemperatureStatusTransitionSelector | IEnumeration    | NormalToHigh
DeviceType                               | IEnumeration    | Transmitter
DeviceUserID                             | IString         |
DeviceVendorName                         | IString         | Baumer
DeviceVersion                            | IString         | R4.4.0
SensorName                               | IString         | IMX265
PixelFormat                              | IEnumeration    | BayerRG8
EnergyEfficientEthernetEnable            | IBoolean        | 1
EventNotification                        | IEnumeration    | Off
EventSelector                            | IEnumeration    | GigEVisionHeartbeatTimeOut
ExposureAutoMaxValue                     | IFloat          | 1e+06
ExposureAutoMinValue                     | IFloat          | 15
ExposureMode                             | IEnumeration    | Timed
ExposureTime                             | IFloat          | 62727
FrameCounter                             | IInteger        | 29849
GVSPConfigurationBlockID64Bit            | IBoolean        | 1
GainAuto                                 | IEnumeration    | Continuous
GevFirstURL                              | IString         | Local:Baumer_VCXG.2-UrFlash_revAB6AC1F56024C846C3D33F6C97360FE710B4843D.zip;10570000;10889
GainAutoMaxValue                         | IFloat          | 251.187
GainAutoMinValue                         | IFloat          | 1
Gamma                                    | IFloat          | 1
LineStatus                               | IBoolean        | 0
GevCCP                                   | IEnumeration    | ControlAccess
GevCurrentDefaultGateway                 | IInteger        | 0.0.0.0
GevCurrentIPAddress                      | IInteger        | 172.31.1.200
GevCurrentIPConfigurationDHCP            | IBoolean        | 1
GevCurrentSubnetMask                     | IInteger        | 255.255.0.0
TriggerSource                            | IEnumeration    | All
GevGVCPExtendedStatusCodes               | IBoolean        | 1
LUTValue                                 | IInteger        | 0
GevGVCPExtendedStatusCodesSelector       | IEnumeration    | Version1_1
UserSetSave                              | ICommand        | [Not Readable]
GevGVCPPendingAck                        | IBoolean        | 1
UserOutputValue                          | IBoolean        | 0
GevIPConfigurationStatus                 | IEnumeration    | PersistentIP
GevInterfaceSelector                     | IInteger        | 0
GevMACAddress                            | IInteger        | 00:06:be:12:b0:06
GevMCDA                                  | IInteger        | 172.31.1.149
boCalibrationMatrixSelector              | IEnumeration    | CameraMatrix
GevMCPHostPort                           | IInteger        | 49158
boGeometryDistortionValue                | IFloat          | 0
GevMCSP                                  | IInteger        | 49151
GevMCTT                                  | IInteger        | 10
GevNumberOfInterfaces                    | IInteger        | 1
GevPersistentDefaultGateway              | IInteger        | 0.0.0.0
GevPersistentSubnetMask                  | IInteger        | 255.255.0.0
GevPrimaryApplicationIPAddress           | IInteger        | 172.31.1.149
GevPrimaryApplicationSocket              | IInteger        | 49156
GevSCDA                                  | IInteger        | 172.31.1.149
GevSCFTD                                 | IInteger        | 0
GevSCPHostPort                           | IInteger        | 49159
GevSCPInterfaceIndex                     | IInteger        | 0
TriggerMode                              | IEnumeration    | Off
LineInverter                             | IBoolean        | 0
GevSCPSDoNotFragment                     | IBoolean        | 1
TriggerSelector                          | IEnumeration    | FrameStart
TimerTriggerActivation                   | IEnumeration    | RisingEdge
GevSCPSFireTestPacket                    | IBoolean        | 0
GevSCSP                                  | IInteger        | 49153
GevSecondURL                             | IString         | File:CXG.xml
GevStreamChannelSelector                 | IInteger        | 0
GevSupportedOption                       | IBoolean        | 1
GevSupportedOptionSelector               | IEnumeration    | IPConfigurationLLA
Height                                   | IInteger        | 1536
HeightMax                                | IInteger        | 1536
ImageData                                | IRegister       | [Not Readable]
InterfaceSpeedMode                       | IEnumeration    | Ethernet1Gbps
LUTContent                               | IEnumeration    | [Not Readable]
LUTEnable                                | IBoolean        | 0
LUTIndex                                 | IInteger        | 0
LUTSelector                              | IEnumeration    | Luminance
LineDebouncerHighTimeAbs                 | IFloat          | 0
LineMode                                 | IEnumeration    | Input
LineSelector                             | IEnumeration    | Line0
UserSetData                              | IRegister       | [Not Readable]
LineSource                               | IEnumeration    | Off
LineStatusAll                            | IInteger        | 0x6
OffsetX                                  | IInteger        | 0
ReadoutMode                              | IEnumeration    | Overlapped
TimerSelector                            | IEnumeration    | Timer1
ReverseX                                 | IBoolean        | 0
ReverseY                                 | IBoolean        | 0
SensorHeight                             | IInteger        | 1536
SensorPixelHeight                        | IFloat          | 3.45
SensorShutterMode                        | IEnumeration    | Global
SensorWidth                              | IInteger        | 2048
SequencerConfigurationMode               | IEnumeration    | Off
SequencerFeatureEnable                   | IBoolean        | 1
SequencerFeatureSelector                 | IEnumeration    | ExposureTime
SequencerMode                            | IEnumeration    | Off
SequencerPathSelector                    | IInteger        | [Not Readable]
SequencerSetActive                       | IInteger        | [Not Readable]
SequencerSetLoad                         | ICommand        | [Not Readable]
SequencerSetNext                         | IInteger        | [Not Readable]
SequencerSetSave                         | ICommand        | [Not Readable]
SequencerSetSelector                     | IInteger        | [Not Readable]
SequencerSetStart                        | IInteger        | [Not Readable]
SequencerTriggerActivation               | IEnumeration    | [Not Readable]
SequencerTriggerSource                   | IEnumeration    | [Not Readable]
ShortExposureTimeEnable                  | IBoolean        | 0
TLParamsLocked                           | IInteger        | 1
TestPattern                              | IEnumeration    | Off
TimerDelay                               | IFloat          | 0
TimerDuration                            | IFloat          | 10
TimerTriggerSource                       | IEnumeration    | Off
TimestampLatch                           | ICommand        | [Not Readable]
TimestampLatchValue                      | IInteger        | 0
TimestampReset                           | ICommand        | [Not Readable]
TriggerActivation                        | IEnumeration    | RisingEdge
TriggerDelay                             | IFloat          | 0
TriggerSoftware                          | ICommand        | [Not Readable]
UserOutputSelector                       | IEnumeration    | UserOutput1
UserSetDataEnable                        | IBoolean        | 0
UserSetDefault                           | IEnumeration    | Default
UserSetFeatureEnable                     | IBoolean        | 1
UserSetLoad                              | ICommand        | [Not Readable]
UserSetSelector                          | IEnumeration    | Default
UserSetStartAddressSelector              | IInteger        | 1
Width                                    | IInteger        | 2048
WidthMax                                 | IInteger        | 2048
boCalibrationAngularAperture             | IFloat          | 0
boCalibrationDataConfigurationMode       | IEnumeration    | Off
boCalibrationDataSave                    | ICommand        | [Not Readable]
boCalibrationFocalLength                 | IFloat          | 0
boCalibrationMatrixValue                 | IFloat          | 0
boCalibrationMatrixValueSelector         | IEnumeration    | Value11
boCalibrationVectorValueSelector         | IEnumeration    | Value1

Total: 249 features matched.
camera> quit
Camera disconnected.
PS C:\Users\andrea\projects\baumer_vcxg232c_test>
(.venv) Stop-Transcript
**********************
Fine trascrizione Windows PowerShell
Ora di fine: 20260323161511
**********************
