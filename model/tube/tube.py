from pytube import YouTube
def tube():
    specific_url = "https://www.youtube.com/shorts/a5eEtN6tYOE"
    yt = YouTube(specific_url)
    yt.streams.filter(file_extension="mp4").first().download(specific_url)

if __name__=='__main__'    :
    tube()