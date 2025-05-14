# OpenSentry Remote Viewer

This is a simple web application that allows you to view your OpenSentry security camera feed from anywhere with an internet connection.

## Features

- Connect to your OpenSentry server from any device with a web browser
- View live security camera feed with object detection
- Fullscreen mode for better viewing
- Automatic reconnection if connection is lost
- Displays detected objects configuration

## How to Use

1. **Start your OpenSentry server** on the device connected to your camera (e.g., Raspberry Pi)
   - Make sure the server is accessible via your network or internet
   - Note down the IP address or domain of your server

2. **Open the Remote Viewer application** on any device
   - You can simply open the `index.html` file in any modern web browser
   - Or host these files on a web server for access from anywhere

3. **Connect to your server**
   - Enter your server URL (e.g., `http://192.168.1.100:8000` for local network)
   - For internet access, enter your public IP or domain (e.g., `http://yourdomain.com:8000`)
   - Click "Connect"

4. **View your security camera feed**
   - Once connected, you'll see your live security camera feed with object detection

## Making Your Server Accessible from the Internet

To access your OpenSentry server from anywhere on the internet, you have several options:

1. **Port Forwarding**: Configure your router to forward port 8000 to the device running the OpenSentry server
   - You'll need to use your public IP address to connect
   - Consider using a dynamic DNS service if your IP changes frequently

2. **VPN**: Set up a VPN server on your network and connect to it first before accessing your local OpenSentry server

3. **Reverse Proxy Services**: Use services like ngrok to create a secure tunnel to your local server

## Security Notice

When exposing your security camera to the internet, always:
- Use strong passwords and authentication methods
- Consider adding additional security layers like HTTPS and authentication
- Keep your software updated with security patches

## Troubleshooting

- **Can't connect to server**: Check your server URL and make sure the server is running
- **No video appears**: Verify that your camera is working properly on the server
- **Video is slow or laggy**: This might be due to network limitations or server performance
