import os, subprocess
from math import floor
from tinyelements.tinyelements_helpers import get_img_seq
from tinyelements.globals import FFMPEG_PATH

def generate_thumb(element_info):
    if 'Global' in element_info['from_dir']:
        element_base_path = os.path.join(element_info['global_lib'], element_info['category'])
    else:
        element_base_path = os.path.join(element_info['show_lib'], element_info['category'])
    

    for element in element_info['element_list']:
        element_path = os.path.join(element_base_path, element)
        element_data = get_img_seq(element_path)

        frames = os.listdir(element_path)
        frames = [os.path.join(element_path, frame) for frame in frames]
        frames = [frame for frame in frames if element_data['extension'] in frame and element in frame]
        frames = get_frame_list(frames)
        frames.sort()

        thumb_name = '.'.join([element, 'gif'])

        generate_gif(frames, os.path.join(element_path, thumb_name))


def generate_gif(frame_list, output_path, framerate=24):
    temp_dir = os.path.dirname(output_path)
    temp_text = os.path.join(temp_dir, 'frame_list.txt')

    # Create a temporary text file to store the frame list
    with open(temp_text, 'w') as f:
        for frame in frame_list:
            f.write("file '{}'\n".format(frame))
            f.write("duration 0.04\n")

    # Execute FFmpeg command
    ffmpeg_cmd = [
        FFMPEG_PATH,
        '-f', 'concat',
        '-safe', '0',
        '-i', temp_text,
        '-vf', 'scale=256:-1',
        '-framerate', str(framerate),
        '-y',
        output_path
    ]
    print(' '.join(ffmpeg_cmd))

    output = subprocess.run(ffmpeg_cmd, capture_output=True)
    print(output.stdout.decode('utf-8'))
    
    # Remove the temporary frame list file
    subprocess.run(['rm', temp_text])


def get_frame_list(all_frames, max_count=100):
    frame_count = len(all_frames)

    if frame_count <= max_count:
        return all_frames
    
    num_list = list(range(max_count))
    result = []
    for i, frame in enumerate(all_frames):
        percent = floor(i / frame_count * 100)
        if percent in num_list:
            result.append(frame)
            num_list.remove(percent)
    return result
