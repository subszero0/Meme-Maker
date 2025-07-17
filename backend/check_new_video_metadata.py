#!/usr/bin/env python3
import json
import subprocess

# Get the NEW video file path
video_path = "/app/clips/2025-06-18/Defiant_Iran_claims_to_gain_control_of_skies_over_Israeli_cities_Arrow_3_fails_Janta_Ka_Reporter_df36d8db-1394-40d0-9b78-243d4de50ead.mp4"

# Run ffprobe to get metadata
cmd = [
    "ffprobe",
    "-v",
    "quiet",
    "-print_format",
    "json",
    "-show_streams",
    "-show_format",
    video_path,
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    metadata = json.loads(result.stdout)

    print("🔍 NEW VIDEO METADATA ANALYSIS")
    print("=" * 50)

    # Extract video stream info
    video_streams = [
        s for s in metadata.get("streams", []) if s.get("codec_type") == "video"
    ]
    if video_streams:
        video_stream = video_streams[0]
        print(
            f'📺 Resolution: {video_stream.get("width")}x{video_stream.get("height")}'
        )
        print(f'🎯 Codec: {video_stream.get("codec_name")}')

        # Check for rotation in tags
        tags = video_stream.get("tags", {})
        if "rotate" in tags:
            print(f'🔄 Rotation tag: {tags["rotate"]}°')

        # Check for display matrix (side data)
        side_data = video_stream.get("side_data_list", [])
        for data in side_data:
            if data.get("side_data_type") == "Display Matrix":
                rotation = data.get("rotation", 0)
                print(f"🔄 Display Matrix rotation: {rotation}°")

        # Check format-level tags
        format_tags = metadata.get("format", {}).get("tags", {})
        if "rotate" in format_tags:
            print(f'🔄 Format rotation tag: {format_tags["rotate"]}°')

        # Print all tags for debugging
        print(f"🏷️ Stream tags: {tags}")
        print(f"🏷️ Format tags: {format_tags}")
        print(f"🏷️ Side data: {side_data}")

        # Summary
        has_rotation = any(
            [
                tags.get("rotate"),
                format_tags.get("rotate"),
                any(
                    data.get("rotation")
                    for data in side_data
                    if data.get("side_data_type") == "Display Matrix"
                ),
            ]
        )

        if has_rotation:
            print("⚠️ NEW VIDEO HAS ROTATION METADATA!")
        else:
            print("✅ NEW VIDEO - NO ROTATION METADATA FOUND")

        print("\n🎯 COMPARISON WITH ORIGINAL:")
        print("Both videos from same source, same processing pipeline")
        print("If both have same rotation issue, problem is systematic")

    else:
        print("❌ No video streams found")

except Exception as e:
    print(f"❌ Error: {e}")
