const WEBRTC_URL = import.meta.env.VITE_WEBRTC_URL || "http://127.0.0.1:8889/cam1/?autoplay=yes&muted=yes&controls=no";

function StreamVideo({ className = "" }) {
  return (
    <div className={`stream-video ${className}`}>
      <iframe
        src={WEBRTC_URL}
        title="CAM-01 live surveillance feed"
        allow="autoplay; fullscreen; picture-in-picture"
        allowFullScreen
      />
    </div>
  );
}

export default StreamVideo;