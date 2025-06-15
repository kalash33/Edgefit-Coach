#!/usr/bin/env python3
"""
Test Desktop Notifications
Simple script to test if desktop notifications are working on Windows/Linux.
"""

try:
    import platform
    if platform.system() == "Windows":
        from win10toast import ToastNotifier
        NOTIFY_AVAILABLE = True
        NOTIFY_TYPE = "windows"
        toaster = ToastNotifier()
        print("✅ Windows desktop notifications enabled")
    else:
        import notify2
        NOTIFY_AVAILABLE = True
        NOTIFY_TYPE = "linux"
        notify2.init("Edgefit-Coach")
        print("✅ Linux desktop notifications enabled")
except ImportError as e:
    NOTIFY_AVAILABLE = False
    NOTIFY_TYPE = None
    print(f"❌ Desktop notifications not available: {e}")
    print("💡 For Windows: pip install win10toast")
    print("💡 For Linux: pip install notify2")
    exit(1)

def show_desktop_notification(title, message, icon="dialog-information", urgency="normal"):
    """Show desktop notification using platform-appropriate method."""
    if not NOTIFY_AVAILABLE:
        return False
    
    try:
        if NOTIFY_TYPE == "windows":
            # Use Windows Toast notifications
            duration = 10 if urgency == "critical" else 8
            toaster.show_toast(
                title=title,
                msg=message,
                duration=duration,
                threaded=True  # Don't block the main thread
            )
            print(f"🔔 Windows notification shown: {title}")
            
        elif NOTIFY_TYPE == "linux":
            # Use notify2 for Linux
            notification = notify2.Notification(title, message, icon)
            notification.set_timeout(8000)
            
            if urgency == "critical":
                notification.set_urgency(notify2.URGENCY_CRITICAL)
            elif urgency == "low":
                notification.set_urgency(notify2.URGENCY_LOW)
            else:
                notification.set_urgency(notify2.URGENCY_NORMAL)
            
            notification.show()
            print(f"🔔 Linux notification shown: {title}")
            
        return True
    except Exception as e:
        print(f"⚠️  Failed to show desktop notification: {e}")
        return False

def main():
    print("🧪 Testing Desktop Notifications...")
    print(f"🖥️  Platform: {platform.system()}")
    print(f"📱 Notification Type: {NOTIFY_TYPE}")
    print("=" * 50)
    
    # Test 1: Good performance notification
    print("📊 Test 1: Good Performance Notification")
    success1 = show_desktop_notification(
        "🤖 AI Posture Coach",
        "Excellent work! Your posture is perfect. Keep it up!\n\n📊 Good: 8 | Slouch: 2 | Performance: 80.0%",
        "dialog-information",
        "low"
    )
    
    if success1:
        print("✅ Good performance notification sent")
    else:
        print("❌ Failed to send good performance notification")
    
    import time
    time.sleep(3)
    
    # Test 2: Warning notification
    print("\n📊 Test 2: Warning Performance Notification")
    success2 = show_desktop_notification(
        "🤖 AI Posture Coach", 
        "Your posture needs attention. Sit up straight and adjust your monitor!\n\n📊 Good: 5 | Slouch: 5 | Performance: 50.0%",
        "dialog-information",
        "normal"
    )
    
    if success2:
        print("✅ Warning notification sent")
    else:
        print("❌ Failed to send warning notification")
    
    time.sleep(3)
    
    # Test 3: Critical notification
    print("\n📊 Test 3: Critical Performance Notification")
    success3 = show_desktop_notification(
        "🤖 AI Posture Coach",
        "URGENT: Poor posture detected! Straighten your back immediately and take a break!\n\n📊 Good: 2 | Slouch: 8 | Performance: 20.0%",
        "dialog-warning",
        "critical"
    )
    
    if success3:
        print("✅ Critical notification sent")
    else:
        print("❌ Failed to send critical notification")
    
    print("\n" + "=" * 50)
    if success1 and success2 and success3:
        print("🎉 All notification tests passed!")
        print("💡 Desktop notifications are working correctly")
        print("👀 Check your system tray/notification area for popup messages")
    else:
        print("⚠️  Some notification tests failed")
        print("💡 Check your system's notification settings")
        if NOTIFY_TYPE == "windows":
            print("🔧 Windows: Check Settings > System > Notifications & actions")
            print("🔧 Make sure notifications are enabled for Python apps")
    
    print("\n📋 If you see desktop notifications, the system is working!")
    print("🚀 You can now run the posture monitoring with notifications enabled")

if __name__ == "__main__":
    main() 