import edge_tts
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip, CompositeVideoClip
import random
import requests
import asyncio
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import textwrap
import html
from datetime import datetime

VOICE = "en-US-EricNeural"

# List of color pairs (background, text)
COLOR_PAIRS = [
    ("#FBEAEB", "#2F3C7E"),  # Blue & Pastel Pink
    ("#101820", "#FEE715"),  # Dark Charcoal & Bright Yellow
    ("#F96167", "#F9E795"),  # Light Red & Yellow
    ("#990011", "#FCF6F5"),  # Cherry Red & Off-White
    ("#8AAAE5", "#FFFFFF"),  # Baby Blue & White
    ("#00246B", "#CADCFC"),  # Dark Blue & Light Blue
    ("#CC313D", "#F7C5CC"),  # Cherry Red & Bubblegum Pink
    ("#2C5F2D", "#97BC62")   # Forest Green & Moss Green
]


async def generate_audio_file(questions):
    """Generate separate audio files for each question and answer."""
    print("Creating Audio")
    for idx, (question, options, answer) in enumerate(questions):
        question_text = html.unescape(f"{question}")
        options_text = "\n".join(
            [f"{chr(65 + i)}) {opt}" for i, opt in enumerate(options)])
        answer_text = html.unescape(f"{answer}")

        # Generate audio for the question and options
        text_intro = f"Question: {question_text} Options: {options_text}"
        communicate_intro = edge_tts.Communicate(
            text_intro, VOICE, rate="+50%")
        await communicate_intro.save(f"TEMP/question_{idx}.mp3")

        # Generate audio for the answer
        communicate_answer = edge_tts.Communicate(
            f"The answer is {answer_text}", VOICE, rate="+50%")
        await communicate_answer.save(f"TEMP/answer_{idx}.mp3")


def generate_audio(questions):
    """Run the async generate_audio_file function."""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(generate_audio_file(questions))


def fetch_trivia_data(category_number, num_questions=4):
    """Fetch trivia data from the Open Trivia Database API."""
    api_url = f"https://opentdb.com/api.php?amount={num_questions}&category={category_number}&type=multiple"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return None


def create_image_with_text(category, question, options, duration, filename, background_color, text_color, countdown_text=None, line_spacing=10, is_answer=False):
    """Create an image with text overlay on a colorful background."""
    # Create a solid color background
    image = Image.new('RGB', (1080, 1920), color=background_color)
    draw = ImageDraw.Draw(image)

    # Try to use the specified font, fallback to a default font if not found
    try:
        font = ImageFont.truetype("fonts/Roboto-Regular.ttf", 60)
        countdown_font = ImageFont.truetype("fonts/Roboto-Bold.ttf", 120)
        category_font = ImageFont.truetype("fonts/Roboto-Bold.ttf", 80)
        # Larger and bolder font for answers
        answer_font = ImageFont.truetype("fonts/Roboto-Bold.ttf", 100)
    except OSError:
        font = ImageFont.truetype("arial.ttf", 60)  # Fallback to Arial
        countdown_font = ImageFont.truetype(
            "arialbd.ttf", 120)  # Fallback to Arial Bold
        category_font = ImageFont.truetype(
            "arialbd.ttf", 80)  # Fallback to Arial Bold
        answer_font = ImageFont.truetype(
            "arialbd.ttf", 100)  # Fallback to Arial Bold

    # Draw the category text
    category_position = (
        (image.width - draw.textbbox((0, 0), category, font=category_font)[2]) // 2, 50)
    draw.text(category_position, category, font=category_font, fill=text_color)

    if is_answer:
        # Draw the answer text
        answer_position = (
            (image.width - draw.textbbox((0, 0), question, font=answer_font)[2]) // 2, (image.height - draw.textbbox((0, 0), question, font=answer_font)[3]) // 2)
        draw.text(answer_position, question, font=answer_font, fill=text_color)
    else:
        # Wrap the question text
        max_width = 30  # Maximum number of characters per line
        wrapped_question = textwrap.fill(question, width=max_width)

        # Wrap the options text
        wrapped_options = "\n".join([textwrap.fill(
            f"{chr(65 + i)}) {opt}", width=max_width) for i, opt in enumerate(options)])

        # Calculate text size and position for the question
        question_lines = wrapped_question.split('\n')
        question_height = sum(draw.textbbox((0, 0), line, font=font)[
                              3] - draw.textbbox((0, 0), line, font=font)[1] + line_spacing for line in question_lines)
        question_width = max(draw.textbbox((0, 0), line, font=font)[
                             2] - draw.textbbox((0, 0), line, font=font)[0] for line in question_lines)
        question_position = ((image.width - question_width) //
                             2, (image.height - question_height) // 3 + 100)

        # Draw the question text
        y = question_position[1]
        for line in question_lines:
            line_width, line_height = draw.textbbox((0, 0), line, font=font)[2] - draw.textbbox((0, 0), line, font=font)[
                0], draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1]
            line_position = ((image.width - line_width) // 2, y)
            draw.text(line_position, line, font=font, fill=text_color)
            y += line_height + line_spacing

        # Calculate text size and position for the options
        options_lines = wrapped_options.split('\n')
        options_height = sum(draw.textbbox((0, 0), line, font=font)[
                             3] - draw.textbbox((0, 0), line, font=font)[1] + line_spacing for line in options_lines)
        options_width = max(draw.textbbox((0, 0), line, font=font)[
                            2] - draw.textbbox((0, 0), line, font=font)[0] for line in options_lines)
        # Add some space between question and options
        options_position = ((image.width - options_width) // 2, y + 20)

        # Draw the options text
        y = options_position[1]
        for line in options_lines:
            line_width, line_height = draw.textbbox((0, 0), line, font=font)[2] - draw.textbbox((0, 0), line, font=font)[
                0], draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1]
            line_position = ((image.width - line_width) // 2, y)
            draw.text(line_position, line, font=font, fill=text_color)
            y += line_height + line_spacing

        # Draw the countdown text if provided
        if countdown_text:
            countdown_position = ((image.width - draw.textbbox((0, 0),
                                  countdown_text, font=countdown_font)[2]) // 2, y + 50)
            draw.text(countdown_position, countdown_text,
                      font=countdown_font, fill=text_color)

    image.save(filename)
    return ImageClip(filename).set_duration(duration)


def cleanup_temp_files():
    """Delete temporary files created during the video generation process."""
    temp_dir = "TEMP"
    for filename in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")


def create_video(quiz_data, video_filename, category):
    """Create a video with questions, options, countdown, and answers."""
    clips = []
    current_time = 0

    for idx, (question, options, answer) in enumerate(quiz_data):
        # Load the audio files
        question_audio = AudioFileClip(f"TEMP/question_{idx}.mp3")
        answer_audio = AudioFileClip(f"TEMP/answer_{idx}.mp3")

        # Select a random color pair
        background_color, text_color = random.choice(COLOR_PAIRS)
        # Create image with question and options text
        question_options_clip = create_image_with_text(category, html.unescape(
            question), options, question_audio.duration, f"TEMP/question_options_{idx}.jpg", background_color, text_color)
        question_options_clip = question_options_clip.set_audio(question_audio)
        clips.append(question_options_clip.set_start(current_time))

        # Create countdown clips within the same frame as the question and options
        for i in range(3, 0, -1):
            countdown_clip = create_image_with_text(category, html.unescape(
                question), options, 1, f"TEMP/countdown_{idx}_{i}.jpg", background_color, text_color, countdown_text=str(i))
            clips.append(countdown_clip.set_start(
                current_time + question_audio.duration + (3 - i)))

        # Create image with answer text
        answer_clip = create_image_with_text(category, html.unescape(answer), [
        ], answer_audio.duration, f"TEMP/answer_{idx}.jpg", background_color, text_color, is_answer=True)
        answer_clip = answer_clip.set_audio(answer_audio)
        clips.append(answer_clip.set_start(
            current_time + question_audio.duration + 3))

        # Update current time
        # question duration + 3s countdown + answer duration
        current_time += question_audio.duration + 3 + answer_audio.duration

    # Concatenate all clips
    video = concatenate_videoclips(clips)

    # Write the video file with GPU acceleration
    video.write_videofile(
        f'Videos/{video_filename}',
        fps=24,
        codec='h264_nvenc',  # Use NVIDIA GPU encoder
        ffmpeg_params=['-preset', 'fast']  # Adjust the preset as needed
    )

    # Cleanup temporary files
    cleanup_temp_files()


def main():
    trivia_data = fetch_trivia_data(
        category_number=random.randint(9, 32), num_questions=4)
    if not trivia_data:
        print("Failed to fetch trivia data after multiple retries.")
        return

    results = trivia_data['results']
    quiz_data = []
    # You can set this dynamically based on the category_number
    category = "General Knowledge"

    for item in results:
        question = html.unescape(item['question'])
        correct_answer = html.unescape(item['correct_answer'])
        incorrect_answers = [html.unescape(ans)
                             for ans in item['incorrect_answers']]
        options = incorrect_answers + [correct_answer]
        random.shuffle(options)
        quiz_data.append((question, options, correct_answer))

    # Generate separate audio files for each question and answer
    generate_audio(quiz_data)

    # Create the video
    video_filename = f"quiz_video_{datetime.now().strftime('%Y%m%d')}.mp4"
    create_video(quiz_data, video_filename, category)


if __name__ == "__main__":
    # Ensure TEMP directory exists
    os.makedirs("TEMP", exist_ok=True)
    main()
