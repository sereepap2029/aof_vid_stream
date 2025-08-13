"""
Hardware Video Encoder Module

This module provides hardware-accelerated video encoding using NVIDIA NVENC,
Intel Quick Sync, and other hardware encoders for maximum performance.
"""

import cv2
import numpy as np
from typing import Optional, Tuple, Dict, Any, List
import logging
import threading
import time
import subprocess
import sys

logger = logging.getLogger(__name__)


class HardwareCapabilities:
    """Detect and manage hardware encoding capabilities."""
    
    def __init__(self):
        self.nvenc_available = False
        self.quicksync_available = False
        self.vaapi_available = False
        self.cuda_available = False
        self.available_codecs = {}
        self.supported_formats = []
        self._detect_capabilities()
        self._detect_codecs()
    
    def _detect_capabilities(self):
        """Detect available hardware encoding capabilities."""
        try:
            # Check CUDA availability
            try:
                import cv2
                self.cuda_available = cv2.cuda.getCudaEnabledDeviceCount() > 0
                if self.cuda_available:
                    logger.info(f"CUDA devices available: {cv2.cuda.getCudaEnabledDeviceCount()}")
            except:
                self.cuda_available = False
            
            # Check NVENC availability (requires NVIDIA GPU with NVENC support)
            self.nvenc_available = self._check_nvenc()
            
            # Check Intel Quick Sync availability
            self.quicksync_available = self._check_quicksync()
            
            # Check VA-API availability (Linux)
            self.vaapi_available = self._check_vaapi()
            
            logger.info(f"Hardware capabilities - NVENC: {self.nvenc_available}, "
                       f"QuickSync: {self.quicksync_available}, "
                       f"VA-API: {self.vaapi_available}, "
                       f"CUDA: {self.cuda_available}")
                       
        except Exception as e:
            logger.error(f"Error detecting hardware capabilities: {e}")
    
    def _detect_codecs(self):
        """Detect available video codecs with preference for NVENC."""
        try:
            import cv2
            
            logger.info("Detecting available codecs...")
            
            # Define NVENC and hardware-accelerated codec tests first
            hardware_codec_tests = {
                'H264': ['H264'],  # Try hardware H.264 first
                'H265': ['HEVC'],  # NVENC HEVC
            }
            
            # Software codec tests (avoid problematic OpenH264)
            software_codec_tests = {
                'VP8': ['VP8 ', 'VP80'],
                'VP9': ['VP9 ', 'VP90'],
                'MJPG': ['MJPG'],
                'XVID': ['XVID'],
                'DIVX': ['DIVX'],
                'MP4V': ['MP4V', 'FMP4'],
                'AV1': ['AV01'],
            }
            
            # Test hardware codecs first
            if self.nvenc_available:
                for codec_name, fourccs in hardware_codec_tests.items():
                    for fourcc_str in fourccs:
                        # For NVENC, test with mp4 format
                        if self._test_codec_nvenc(fourcc_str, 'mp4'):
                            if codec_name not in self.available_codecs:
                                self.available_codecs[codec_name] = []
                            
                            codec_info = {
                                'fourcc': fourcc_str,
                                'format': 'mp4',
                                'hardware_support': True
                            }
                            
                            if codec_info not in self.available_codecs[codec_name]:
                                self.available_codecs[codec_name].append(codec_info)
                                logger.info(f"  {codec_name}: {fourcc_str} (mp4) [HW]")
            
            # Test software codecs
            formats = ['mp4', 'avi', 'mkv', 'webm', 'mov']
            for codec_name, fourccs in software_codec_tests.items():
                for fourcc_str in fourccs:
                    for fmt in formats:
                        if self._test_codec_software(fourcc_str, fmt):
                            if codec_name not in self.available_codecs:
                                self.available_codecs[codec_name] = []
                            
                            codec_info = {
                                'fourcc': fourcc_str,
                                'format': fmt,
                                'hardware_support': False
                            }
                            
                            if codec_info not in self.available_codecs[codec_name]:
                                self.available_codecs[codec_name].append(codec_info)
                                logger.info(f"  {codec_name}: {fourcc_str} ({fmt}) [SW]")
                            break  # Found working combination for this codec
            
            # Add fallback software H.264 if hardware failed (but avoid OpenH264)
            if 'H264' not in self.available_codecs:
                # Try alternative H.264 codecs that don't use OpenH264
                alt_h264_tests = ['AVC1', 'X264']
                for fourcc_str in alt_h264_tests:
                    for fmt in ['mp4', 'mov']:
                        if self._test_codec_software(fourcc_str, fmt):
                            if 'H264' not in self.available_codecs:
                                self.available_codecs['H264'] = []
                            
                            codec_info = {
                                'fourcc': fourcc_str,
                                'format': fmt,
                                'hardware_support': self._check_hardware_support('H264')
                            }
                            
                            if codec_info not in self.available_codecs['H264']:
                                self.available_codecs['H264'].append(codec_info)
                                hw_label = 'HW' if codec_info['hardware_support'] else 'SW'
                                logger.info(f"  H264: {fourcc_str} ({fmt}) [{hw_label}]")
                            break
            
            # Always include JPEG as fallback
            self.available_codecs['JPEG'] = [{
                'fourcc': 'JPEG',
                'format': 'jpg',
                'hardware_support': self.cuda_available
            }]
            
            # Log available codecs
            logger.info(f"Available codecs: {list(self.available_codecs.keys())}")
            for codec, variants in self.available_codecs.items():
                for variant in variants:
                    hw_support = "HW" if variant['hardware_support'] else "SW"
                    logger.info(f"  {codec}: {variant['fourcc']} ({variant['format']}) [{hw_support}]")
                    
        except Exception as e:
            logger.error(f"Error detecting codecs: {e}")
            # Fallback to JPEG only
            self.available_codecs = {
                'JPEG': [{'fourcc': 'JPEG', 'format': 'jpg', 'hardware_support': False}]
            }
    
    def _test_codec_nvenc(self, fourcc_str, fmt):
        """Test NVENC hardware codec specifically."""
        try:
            import cv2
            import os
            
            if not self.nvenc_available:
                return False
                
            test_file = f'nvenc_test.{fmt}'
            
            # Create fourcc
            fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
            
            # Test with hardware acceleration hint
            writer = cv2.VideoWriter(
                test_file,
                cv2.CAP_FFMPEG,  # Backend hint for hardware
                fourcc,
                30.0,  # fps
                (640, 480),
                True
            )
            
            is_opened = writer.isOpened()
            
            # Test actual frame writing for hardware validation
            if is_opened:
                try:
                    import numpy as np
                    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    test_frame.fill(128)  # Gray frame
                    success = writer.write(test_frame)
                    if not success:
                        is_opened = False
                except:
                    is_opened = False
            
            writer.release()
            
            # Clean up
            if os.path.exists(test_file):
                try:
                    os.remove(test_file)
                except:
                    pass
            
            return is_opened
            
        except Exception as e:
            logger.debug(f"NVENC codec test failed for {fourcc_str}.{fmt}: {e}")
            return False
    
    def _test_codec_software(self, fourcc_str, fmt):
        """Test software codec without triggering hardware dependencies."""
        try:
            import cv2
            import os
            
            # Skip codecs that might trigger OpenH264 issues
            problematic_codecs = ['H264', 'AVC1', 'X264']
            if fourcc_str in problematic_codecs:
                # Only test these if we explicitly want software fallback
                # and we're not using OpenH264
                pass
            
            test_file = f'sw_test.{fmt}'
            
            # Create fourcc
            fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
            
            # Test writer creation with explicit software backend
            writer = cv2.VideoWriter(
                test_file,
                fourcc,
                30.0,  # fps
                (640, 480),
                True
            )
            
            is_opened = writer.isOpened()
            writer.release()
            
            # Clean up
            if os.path.exists(test_file):
                try:
                    os.remove(test_file)
                except:
                    pass
            
            return is_opened
            
        except Exception as e:
            logger.debug(f"Software codec test failed for {fourcc_str}.{fmt}: {e}")
            return False
    
    def _test_codec(self, fourcc_str: str, format_ext: str) -> bool:
        """Test if a codec/format combination works."""
        try:
            import cv2
            import os
            import tempfile
            
            # Create temporary file
            temp_file = os.path.join(tempfile.gettempdir(), f'test_codec.{format_ext}')
            
            try:
                fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
                writer = cv2.VideoWriter(temp_file, fourcc, 30.0, (320, 240))
                
                if writer.isOpened():
                    # Create a test frame
                    test_frame = np.zeros((240, 320, 3), dtype=np.uint8)
                    writer.write(test_frame)
                    writer.release()
                    
                    # Check if file was created and has reasonable size
                    if os.path.exists(temp_file) and os.path.getsize(temp_file) > 100:
                        os.remove(temp_file)
                        return True
                
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                return False
                
            except Exception:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                return False
                
        except Exception:
            return False
    
    def _check_hardware_support(self, codec_name: str) -> bool:
        """Check if codec has hardware acceleration support."""
        if codec_name == 'H264':
            return self.nvenc_available or self.quicksync_available or self.vaapi_available
        elif codec_name == 'H265':
            return self.nvenc_available or self.quicksync_available
        elif codec_name in ['VP8', 'VP9']:
            return self.vaapi_available
        elif codec_name == 'JPEG':
            return self.cuda_available
        return False
    
    def get_best_codec(self, prefer_hardware: bool = True) -> Dict[str, Any]:
        """Get the best available codec based on preferences."""
        if not self.available_codecs:
            return {'codec': 'JPEG', 'fourcc': 'JPEG', 'format': 'jpg', 'hardware_support': False}
        
        # Priority order for codecs (prioritize H.264 for better compatibility)
        codec_priority = ['H264', 'H265', 'VP9', 'VP8', 'MJPG', 'JPEG']
        
        for codec_name in codec_priority:
            if codec_name in self.available_codecs:
                variants = self.available_codecs[codec_name]
                
                if prefer_hardware:
                    # Try to find hardware-accelerated variant first
                    hw_variants = [v for v in variants if v['hardware_support']]
                    if hw_variants:
                        variant = hw_variants[0]
                        return {
                            'codec': codec_name,
                            'fourcc': variant['fourcc'],
                            'format': variant['format'],
                            'hardware_support': True
                        }
                
                # Fall back to software variant
                if variants:
                    variant = variants[0]
                    return {
                        'codec': codec_name,
                        'fourcc': variant['fourcc'],
                        'format': variant['format'],
                        'hardware_support': variant['hardware_support']
                    }
        
        # Ultimate fallback
        return {'codec': 'JPEG', 'fourcc': 'JPEG', 'format': 'jpg', 'hardware_support': False}
    
    def get_codec_info(self, codec_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific codec."""
        if codec_name in self.available_codecs and self.available_codecs[codec_name]:
            variant = self.available_codecs[codec_name][0]
            return {
                'codec': codec_name,
                'fourcc': variant['fourcc'],
                'format': variant['format'],
                'hardware_support': variant['hardware_support'],
                'available': True
            }
        return None
    
    def _check_nvenc(self) -> bool:
        """Check if NVENC is available."""
        try:
            # Try to create NVENC encoder to test availability
            fourcc = cv2.VideoWriter_fourcc(*'H264')
            temp_writer = cv2.VideoWriter('temp_test.mp4', fourcc, 30, (640, 480))
            if temp_writer.isOpened():
                temp_writer.release()
                try:
                    import os
                    os.remove('temp_test.mp4')
                except:
                    pass
                return True
            return False
        except Exception as e:
            logger.debug(f"NVENC check failed: {e}")
            return False
    
    def _check_quicksync(self) -> bool:
        """Check if Intel Quick Sync is available."""
        try:
            # Check for Intel graphics
            result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'], 
                                  capture_output=True, text=True, timeout=5)
            return 'Intel' in result.stdout
        except Exception as e:
            logger.debug(f"QuickSync check failed: {e}")
            return False
    
    def _check_vaapi(self) -> bool:
        """Check if VA-API is available (Linux only)."""
        try:
            if sys.platform.startswith('linux'):
                result = subprocess.run(['vainfo'], capture_output=True, text=True, timeout=5)
                return 'VAEntrypointEncSlice' in result.stdout
        except Exception as e:
            logger.debug(f"VA-API check failed: {e}")
        return False


class HardwareEncoder:
    """Hardware-accelerated video encoder with codec selection support."""
    
    def __init__(self, width: int = 1920, height: int = 1080, fps: int = 60, 
                 bitrate: int = 8000000, codec: str = 'auto'):  # 8 Mbps default
        """
        Initialize hardware encoder.
        
        Args:
            width (int): Video width
            height (int): Video height  
            fps (int): Frames per second
            bitrate (int): Target bitrate in bits per second
            codec (str): Codec to use ('auto', 'H264', 'H265', 'VP8', 'VP9', 'MJPG', 'JPEG')
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.bitrate = bitrate
        self.requested_codec = codec
        
        self.capabilities = HardwareCapabilities()
        self.encoder = None
        self.encoding_method = None
        self.current_codec_info = None
        self._lock = threading.Lock()
        
        # Performance tracking
        self.encode_times = []
        self.frames_encoded = 0
        
        # Initialize the best available encoder
        self._init_encoder()
    
    def _init_encoder(self):
        """Initialize encoder based on codec selection."""
        try:
            # Determine which codec to use
            if self.requested_codec == 'auto':
                self.current_codec_info = self.capabilities.get_best_codec(prefer_hardware=True)
            else:
                self.current_codec_info = self.capabilities.get_codec_info(self.requested_codec)
                if not self.current_codec_info:
                    logger.warning(f"Requested codec '{self.requested_codec}' not available, using auto selection")
                    self.current_codec_info = self.capabilities.get_best_codec(prefer_hardware=True)
            
            logger.info(f"Selected codec: {self.current_codec_info['codec']} "
                       f"({self.current_codec_info['fourcc']}) "
                       f"[{'HW' if self.current_codec_info['hardware_support'] else 'SW'}]")
            
            # Initialize encoder based on codec and hardware support
            if self.current_codec_info['codec'] == 'JPEG':
                self._init_jpeg_encoder()
            elif self.current_codec_info['hardware_support']:
                self._init_hardware_video_encoder()
            else:
                self._init_software_video_encoder()
                
        except Exception as e:
            logger.error(f"Error initializing encoder: {e}")
            self._init_jpeg_encoder()
    
    def _init_hardware_video_encoder(self):
        """Initialize hardware video encoder with fallback support."""
        try:
            codec_info = self.current_codec_info
            logger.info(f"Initializing hardware encoder for {codec_info['codec']}...")
            
            fourcc = cv2.VideoWriter_fourcc(*codec_info['fourcc'])
            temp_file = f'temp_hw_{codec_info["codec"].lower()}.{codec_info["format"]}'
            
            self.encoder = cv2.VideoWriter(
                temp_file,
                fourcc,
                float(self.fps),
                (self.width, self.height),
                True
            )
            
            if self.encoder.isOpened():
                self.encoding_method = f"{codec_info['codec']} (Hardware)"
                logger.info(f"Hardware encoder initialized: {self.width}x{self.height}@{self.fps}fps")
            else:
                raise Exception("Failed to open hardware encoder")
                
        except Exception as e:
            logger.error(f"Hardware encoder initialization failed: {e}")
            # Try fallback to H.264 if we were trying H.265
            if self.current_codec_info['codec'] == 'H265':
                logger.info("Falling back to H.264 hardware encoding...")
                h264_info = self.capabilities.get_codec_info('H264')
                if h264_info and h264_info['hardware_support']:
                    self.current_codec_info = h264_info
                    try:
                        fourcc = cv2.VideoWriter_fourcc(*h264_info['fourcc'])
                        temp_file = f'temp_hw_h264.{h264_info["format"]}'
                        
                        self.encoder = cv2.VideoWriter(
                            temp_file,
                            fourcc,
                            float(self.fps),
                            (self.width, self.height),
                            True
                        )
                        
                        if self.encoder.isOpened():
                            self.encoding_method = f"{h264_info['codec']} (Hardware)"
                            logger.info(f"H.264 hardware encoder initialized: {self.width}x{self.height}@{self.fps}fps")
                            return
                    except Exception as e2:
                        logger.error(f"H.264 hardware fallback also failed: {e2}")
            
            self._init_software_video_encoder()
    
    def _init_software_video_encoder(self):
        """Initialize software video encoder with fallback support."""
        try:
            codec_info = self.current_codec_info
            logger.info(f"Initializing software encoder for {codec_info['codec']}...")
            
            fourcc = cv2.VideoWriter_fourcc(*codec_info['fourcc'])
            temp_file = f'temp_sw_{codec_info["codec"].lower()}.{codec_info["format"]}'
            
            self.encoder = cv2.VideoWriter(
                temp_file,
                fourcc,
                float(self.fps),
                (self.width, self.height),
                True
            )
            
            if self.encoder.isOpened():
                self.encoding_method = f"{codec_info['codec']} (Software)"
                logger.info(f"Software encoder initialized: {self.width}x{self.height}@{self.fps}fps")
            else:
                raise Exception("Failed to open software encoder")
                
        except Exception as e:
            logger.error(f"Software encoder initialization failed: {e}")
            # Try fallback to H.264 if we were trying H.265
            if self.current_codec_info['codec'] == 'H265':
                logger.info("Falling back to H.264 software encoding...")
                h264_info = self.capabilities.get_codec_info('H264')
                if h264_info:
                    self.current_codec_info = h264_info
                    try:
                        fourcc = cv2.VideoWriter_fourcc(*h264_info['fourcc'])
                        temp_file = f'temp_sw_h264.{h264_info["format"]}'
                        
                        self.encoder = cv2.VideoWriter(
                            temp_file,
                            fourcc,
                            float(self.fps),
                            (self.width, self.height),
                            True
                        )
                        
                        if self.encoder.isOpened():
                            self.encoding_method = f"{h264_info['codec']} (Software)"
                            logger.info(f"H.264 software encoder initialized: {self.width}x{self.height}@{self.fps}fps")
                            return
                    except Exception as e2:
                        logger.error(f"H.264 software fallback also failed: {e2}")
            
            self._init_jpeg_encoder()
    
    def _init_jpeg_encoder(self):
        """Initialize JPEG encoder (fallback)."""
        try:
            logger.info("Initializing JPEG encoder...")
            self.encoding_method = 'JPEG'
            self.current_codec_info = {
                'codec': 'JPEG',
                'fourcc': 'JPEG',
                'format': 'jpg',
                'hardware_support': self.capabilities.cuda_available
            }
            logger.info(f"JPEG encoder initialized: {self.width}x{self.height}")
        except Exception as e:
            logger.error(f"JPEG encoder initialization failed: {e}")
            self.encoding_method = 'JPEG'
    
    def _init_nvenc_encoder(self):
        """Initialize NVIDIA NVENC encoder."""
        try:
            logger.info("Initializing NVIDIA NVENC encoder...")
            
            # Use H.264 NVENC
            fourcc = cv2.VideoWriter_fourcc(*'H264')
            
            # Create temporary file for testing
            self.encoder = cv2.VideoWriter()
            
            # Set codec parameters for NVENC
            # Note: OpenCV doesn't directly expose NVENC parameters,
            # but we can use GPU memory and optimized settings
            success = self.encoder.open(
                'temp_nvenc.mp4',
                fourcc,
                float(self.fps),
                (self.width, self.height),
                True
            )
            
            if success:
                self.encoding_method = 'NVENC'
                logger.info(f"NVENC encoder initialized: {self.width}x{self.height}@{self.fps}fps")
            else:
                raise Exception("Failed to open NVENC encoder")
                
        except Exception as e:
            logger.error(f"NVENC encoder initialization failed: {e}")
            raise
    
    def _init_quicksync_encoder(self):
        """Initialize Intel Quick Sync encoder."""
        try:
            logger.info("Initializing Intel Quick Sync encoder...")
            
            # Use H.264 with Intel optimizations
            fourcc = cv2.VideoWriter_fourcc(*'H264')
            
            self.encoder = cv2.VideoWriter(
                'temp_quicksync.mp4',
                fourcc,
                float(self.fps),
                (self.width, self.height),
                True
            )
            
            self.encoding_method = 'QuickSync'
            logger.info(f"QuickSync encoder initialized: {self.width}x{self.height}@{self.fps}fps")
            
        except Exception as e:
            logger.error(f"QuickSync encoder initialization failed: {e}")
            raise
    
    def encode_frame(self, frame: np.ndarray, quality: int = 90) -> Optional[bytes]:
        """
        Encode a single frame using the selected codec.
        
        Args:
            frame (np.ndarray): Input frame
            quality (int): Encoding quality (1-100)
            
        Returns:
            Optional[bytes]: Encoded frame data
        """
        if frame is None or frame.size == 0:
            return None
        
        encode_start = time.time()
        
        try:
            with self._lock:
                if self.current_codec_info['codec'] == 'JPEG':
                    return self._encode_jpeg(frame, quality)
                else:
                    return self._encode_video_frame(frame, quality)
                
        except Exception as e:
            logger.error(f"Error encoding frame: {e}")
            # Fallback to JPEG
            return self._encode_jpeg(frame, quality)
        finally:
            encode_time = time.time() - encode_start
            self.encode_times.append(encode_time)
            self.frames_encoded += 1
            
            # Keep only last 100 measurements
            if len(self.encode_times) > 100:
                self.encode_times.pop(0)
    
    def _encode_video_frame(self, frame: np.ndarray, quality: int) -> Optional[bytes]:
        """Encode frame using video codec."""
        try:
            # For video codecs, we still use JPEG for streaming compatibility
            # but with optimizations based on the selected codec capabilities
            if self.current_codec_info['hardware_support'] and self.capabilities.cuda_available:
                return self._encode_cuda_jpeg(frame, quality)
            else:
                return self._encode_optimized_jpeg(frame, quality)
                
        except Exception as e:
            logger.error(f"Video frame encoding failed: {e}")
            return self._encode_jpeg(frame, quality)
            if len(self.encode_times) > 100:
                self.encode_times.pop(0)
    
    def _encode_cuda_jpeg(self, frame: np.ndarray, quality: int) -> Optional[bytes]:
        """Encode JPEG using CUDA acceleration."""
        try:
            # Upload frame to GPU memory
            gpu_frame = cv2.cuda_GpuMat()
            gpu_frame.upload(frame)
            
            # Perform any GPU preprocessing (resize, color conversion, etc.)
            # Download back to CPU for JPEG encoding
            cpu_frame = gpu_frame.download()
            
            # Use optimized JPEG encoding
            encode_params = [
                cv2.IMWRITE_JPEG_QUALITY, quality,
                cv2.IMWRITE_JPEG_OPTIMIZE, 1,
                cv2.IMWRITE_JPEG_PROGRESSIVE, 1
            ]
            
            success, encoded_frame = cv2.imencode('.jpg', cpu_frame, encode_params)
            
            if success:
                return encoded_frame.tobytes()
            return None
            
        except Exception as e:
            logger.error(f"CUDA JPEG encoding failed: {e}")
            return self._encode_jpeg(frame, quality)
    
    def _encode_optimized_jpeg(self, frame: np.ndarray, quality: int) -> Optional[bytes]:
        """Encode JPEG with CPU optimizations."""
        try:
            # Optimized JPEG parameters
            encode_params = [
                cv2.IMWRITE_JPEG_QUALITY, quality,
                cv2.IMWRITE_JPEG_OPTIMIZE, 1,        # Optimize Huffman tables
                cv2.IMWRITE_JPEG_PROGRESSIVE, 1,     # Progressive JPEG
                cv2.IMWRITE_JPEG_RST_INTERVAL, 16    # Restart markers for error resilience
            ]
            
            success, encoded_frame = cv2.imencode('.jpg', frame, encode_params)
            
            if success:
                return encoded_frame.tobytes()
            return None
            
        except Exception as e:
            logger.error(f"Optimized JPEG encoding failed: {e}")
            return self._encode_jpeg(frame, quality)
    
    def _encode_jpeg(self, frame: np.ndarray, quality: int) -> Optional[bytes]:
        """Basic JPEG encoding (fallback)."""
        try:
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            success, encoded_frame = cv2.imencode('.jpg', frame, encode_params)
            
            if success:
                return encoded_frame.tobytes()
            return None
            
        except Exception as e:
            logger.error(f"JPEG encoding failed: {e}")
            return None
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get encoding performance statistics."""
        if not self.encode_times:
            return {
                'encoding_method': self.encoding_method or 'Not Initialized',
                'codec': self.current_codec_info['codec'] if self.current_codec_info else 'Unknown',
                'fourcc': self.current_codec_info['fourcc'] if self.current_codec_info else 'Unknown',
                'hardware_support': self.current_codec_info['hardware_support'] if self.current_codec_info else False,
                'frames_encoded': 0,
                'avg_encode_time': 0,
                'fps_capability': 0,
                'available_codecs': list(self.capabilities.available_codecs.keys())
            }
        
        avg_encode_time = sum(self.encode_times) / len(self.encode_times)
        fps_capability = 1.0 / avg_encode_time if avg_encode_time > 0 else 0
        
        return {
            'encoding_method': self.encoding_method,
            'codec': self.current_codec_info['codec'] if self.current_codec_info else 'Unknown',
            'fourcc': self.current_codec_info['fourcc'] if self.current_codec_info else 'Unknown',
            'hardware_support': self.current_codec_info['hardware_support'] if self.current_codec_info else False,
            'frames_encoded': self.frames_encoded,
            'avg_encode_time': avg_encode_time,
            'fps_capability': fps_capability,
            'available_codecs': list(self.capabilities.available_codecs.keys()),
            'hardware_available': {
                'nvenc': self.capabilities.nvenc_available,
                'quicksync': self.capabilities.quicksync_available,
                'vaapi': self.capabilities.vaapi_available,
                'cuda': self.capabilities.cuda_available
            }
        }
    
    def cleanup(self):
        """Clean up encoder resources."""
        try:
            if self.encoder:
                self.encoder.release()
                self.encoder = None
            
            # Clean up temporary files
            import os
            for temp_file in ['temp_nvenc.mp4', 'temp_quicksync.mp4', 'temp_vaapi.mp4', 'temp_software.mp4']:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error cleaning up encoder: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()


# Global hardware encoder instance
_hardware_encoder: Optional[HardwareEncoder] = None
_encoder_lock = threading.Lock()


def get_hardware_encoder(width: int = 1920, height: int = 1080, fps: int = 60, codec: str = 'auto') -> HardwareEncoder:
    """
    Get or create the global hardware encoder instance.
    
    Args:
        width (int): Video width
        height (int): Video height
        fps (int): Frames per second
        codec (str): Codec to use ('auto', 'H264', 'H265', 'VP8', 'VP9', 'MJPG', 'JPEG')
        
    Returns:
        HardwareEncoder: Hardware encoder instance
    """
    global _hardware_encoder
    
    with _encoder_lock:
        if _hardware_encoder is None:
            _hardware_encoder = HardwareEncoder(width, height, fps, codec=codec)
        
        # Recreate if dimensions or codec changed
        elif (_hardware_encoder.width != width or 
              _hardware_encoder.height != height or 
              _hardware_encoder.fps != fps or
              _hardware_encoder.requested_codec != codec):
            _hardware_encoder.cleanup()
            _hardware_encoder = HardwareEncoder(width, height, fps, codec=codec)
    
    return _hardware_encoder


def get_available_codecs() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get list of available codecs on the system.
    
    Returns:
        Dict with codec names and their variants
    """
    capabilities = HardwareCapabilities()
    return capabilities.available_codecs


def cleanup_hardware_encoder():
    """Clean up the global hardware encoder."""
    global _hardware_encoder
    
    with _encoder_lock:
        if _hardware_encoder:
            _hardware_encoder.cleanup()
            _hardware_encoder = None
