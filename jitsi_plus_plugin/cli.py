# jitsi_plus_plugin/cli.py

import argparse
import sys
import logging
from .version import __version__
from . import JitsiPlusPlugin

logger = logging.getLogger(__name__)

def setup_parser():
    """Set up the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        description="Jitsi Plus Plugin - Comprehensive Jitsi integration for Python",
        prog="jitsi-plus"
    )

    parser.add_argument(
        '--version', '-v', action='version',
        version=f'%(prog)s {__version__}'
    )
    
    parser.add_argument(
        '--debug', action='store_true',
        help='Enable debug logging'
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Create video call command
    create_call_parser = subparsers.add_parser('create-call', help='Create a video call')
    create_call_parser.add_argument('--max-participants', type=int, default=10, help='Maximum number of participants')
    create_call_parser.add_argument('--features', nargs='+', default=['video', 'audio', 'chat'], 
                                  help='Features to enable (video, audio, chat, whiteboard, polls, screen_sharing)')
    
    # Create audio call command
    create_audio_parser = subparsers.add_parser('create-audio-call', help='Create an audio-only call')
    create_audio_parser.add_argument('--max-participants', type=int, default=10, help='Maximum number of participants')
    create_audio_parser.add_argument('--features', nargs='+', default=['audio', 'chat'], 
                                   help='Features to enable (audio, chat, polls)')
    
    # Create broadcast command
    create_broadcast_parser = subparsers.add_parser('create-broadcast', help='Create a broadcast')
    create_broadcast_parser.add_argument('name', help='Name of the broadcast')
    create_broadcast_parser.add_argument('--max-hosts', type=int, default=2, help='Maximum number of hosts')
    create_broadcast_parser.add_argument('--record', action='store_true', help='Enable recording')
    
    # List calls command
    list_calls_parser = subparsers.add_parser('list-calls', help='List active calls')
    
    # Start media server command
    start_media_parser = subparsers.add_parser('start-media-server', help='Start a media server')
    start_media_parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    start_media_parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    
    # VOD commands
    vod_parser = subparsers.add_parser('vod', help='Video on Demand operations')
    vod_subparsers = vod_parser.add_subparsers(dest='vod_command', help='VOD command to run')
    
    # Create VOD entry
    create_vod_parser = vod_subparsers.add_parser('create', help='Create a VOD entry')
    create_vod_parser.add_argument('name', help='Name of the VOD entry')
    create_vod_parser.add_argument('file_path', help='Path to the video file')
    
    # List VOD entries
    list_vod_parser = vod_subparsers.add_parser('list', help='List VOD entries')
    
    return parser

def main():
    """Main entry point for the CLI."""
    parser = setup_parser()
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize the plugin
    try:
        plugin = JitsiPlusPlugin()
        plugin.initialize()
        
        # Handle commands
        if args.command == 'create-call':
            # Convert features list to dictionary
            features = {feature: True for feature in args.features}
            
            call_info = plugin.video_call.create_call({
                "max_participants": args.max_participants,
                "features": features
            })
            
            print(f"Video call created successfully:")
            print(f"  ID: {call_info['id']}")
            print(f"  URL: {call_info['jitsi_url']}")
            print(f"  Features: {', '.join(call_info['features'].keys())}")
        
        elif args.command == 'create-audio-call':
            # Convert features list to dictionary
            features = {feature: True for feature in args.features}
            
            call_info = plugin.audio_call.create_call({
                "max_participants": args.max_participants,
                "features": features
            })
            
            print(f"Audio call created successfully:")
            print(f"  ID: {call_info['id']}")
            print(f"  URL: {call_info['jitsi_url']}")
            print(f"  Features: {', '.join(call_info['features'].keys())}")
        
        elif args.command == 'create-broadcast':
            # Create broadcast
            broadcast_info = plugin.broadcast.create_broadcast(args.name, {
                "max_hosts": args.max_hosts,
                "recording": args.record
            })
            
            # Start broadcast
            plugin.broadcast.start_broadcast(broadcast_info['id'])
            
            print(f"Broadcast '{args.name}' created and started:")
            print(f"  ID: {broadcast_info['id']}")
            print(f"  RTMP URL: {broadcast_info['rtmp_url']}")
            print(f"  HLS URL: {broadcast_info['hls_url']}")
            print(f"  Recording: {'Enabled' if args.record else 'Disabled'}")
        
        elif args.command == 'list-calls':
            # List video calls
            video_calls = plugin.video_call.list_active_calls()
            
            # List audio calls
            audio_calls = plugin.audio_call.list_active_calls()
            
            # List broadcasts
            broadcasts = plugin.broadcast.list_active_broadcasts()
            
            print(f"Active Video Calls: {len(video_calls)}")
            for call in video_calls:
                print(f"  {call['id']} - Participants: {len(call['participants'])}")
            
            print(f"\nActive Audio Calls: {len(audio_calls)}")
            for call in audio_calls:
                print(f"  {call['id']} - Participants: {len(call['participants'])}")
            
            print(f"\nActive Broadcasts: {len(broadcasts)}")
            for broadcast in broadcasts:
                print(f"  {broadcast['id']} - '{broadcast['name']}' - Viewers: {broadcast['viewers']}")
        
        elif args.command == 'start-media-server':
            print(f"Starting media server on {args.host}:{args.port}...")
            
            # Configure media server
            plugin.media_server.config['host'] = args.host
            plugin.media_server.config['port'] = args.port
            
            # This would typically block until terminated
            print("Media server is running. Press Ctrl+C to stop.")
            try:
                import asyncio
                asyncio.get_event_loop().run_forever()
            except KeyboardInterrupt:
                print("Shutting down media server...")
        
        elif args.command == 'vod':
            if args.vod_command == 'create':
                vod_info = plugin.vod.create_vod_entry(args.name, args.file_path)
                print(f"VOD entry created:")
                print(f"  ID: {vod_info['id']}")
                print(f"  Name: {vod_info['name']}")
                print(f"  URL: {vod_info['url']}")
            
            elif args.vod_command == 'list':
                vod_entries = plugin.vod.list_vod_entries()
                print(f"VOD Entries: {len(vod_entries)}")
                for entry in vod_entries:
                    print(f"  {entry['id']} - '{entry['name']}'")
            
            else:
                print("Unknown VOD command. Use 'jitsi-plus vod --help' for more information.")
        
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    finally:
        # Shutdown the plugin if needed
        if 'plugin' in locals():
            plugin.shutdown()

if __name__ == "__main__":
    main()