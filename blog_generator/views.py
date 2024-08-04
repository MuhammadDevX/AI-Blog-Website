from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from pytube import YouTube
from django.conf import settings
import os
import assemblyai as aai
import openai 
from .models import BlogPost
# Create your views here.
@login_required
def index (request):
  return render(request,"../templates/index.html") 


def login_page(request):
  if request.method == "POST":
    username = request.POST["username"]
    password = request.POST["password"]
    user = authenticate(request,username=username,password=password)
    if user is not None:
      login(request,user)
      return redirect("/")
    else:
      error_message = "Username or Password is incorrect"
      return render(request,"../templates/login.html",{"error_message":error_message})
  return render(request,"../templates/login.html")


def get_Title(link):
  yt = YouTube(link)
  return yt.title



def signup_page(request):
  if request.method == "POST":
    username = request.POST["username"]
    email = request.POST["email"]
    password = request.POST["password"]
    confirm_password = request.POST["confirm-password"]
    
     
    if password == confirm_password:
      try:
        user = User.objects.create_user(username,email,password)
        user.save()
        login(request,user)
        return redirect("/")
      except:
        error_message ="User already exists"
        return render(request,"../templates/signup.html",{"error_message":error_message})
    else:
      error_message ="Passwords do not match"
      return render(request,"../templates/signup.html",{"error_message":error_message})

  return render(request,"../templates/signup.html")

def logout_page(request):
  logout(request)
  return redirect("/")




def download_audio(link):
  yt = YouTube(link)
  
  # print(yt.title)
  videos = yt.streams.filter(only_audio=True,use_oath = False, allow_oauth_cache=True)  
  # video = yt.streams.filter(only_audio=True).first()
  video = videos.first()
  # print(video.abr)
  out_file = video.download(output_path=settings.MEDIA_ROOT)
  base, ext = os.path.splitext(out_file) 
  new_file = base + ".mp3"
  os.rename(out_file,new_file)
  return new_file

def get_transcription(link):
  audio_file = download_audio(link)
  aai.settings.api_key ="your-key"
  transcriber = aai.Transcriber()
  transcript = transcriber.transcribe(audio_file)
  return transcript.text
  
def generate_blog_from_transcript(transcript):
  openai.api_key = "your-key"
  prompt = f"Based on the following transcript from a youtube video, write a comprehensive blog based on the transcript, but do not make it look like a youtube video, make it look like a blog post. \n\n {transcript} \n\nArticle:"
  response = openai.Completion.create(
    engine="text-davinci-003",
    prompt=prompt,
    max_tokens=1000
  )
  return response.choices[0].text.strip()




# @csrf_exempt
# def generate_blogs(request):
#   if request.method == "POST":
#     try:
#       data = json.loads(request.body)
#       yt_link = data["link"]
      
#     except (KeyError, json.JSONDecodeError):
#       return JsonResponse({"error":"Invalid Data sent"},status=400)
      
#     yt_title = get_Title(yt_link)
    
#     transcription = get_transcription(yt_link)
#     print("I am after transcription")
#     if not transcription:
#       return JsonResponse({"error":"Transcription failed"},status=500)
    
#     blog_content = generate_blog_from_transcript(transcription)
#     if not blog_content:
#       return JsonResponse({"error":"Blog Generation failed"},status=500)
    
#     return JsonResponse({"content":blog_content})
#   else:
#     return JsonResponse({"error":"Invalid Request Method"},status=405)

@csrf_exempt
def generate_blogs(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            yt_link = data.get("link", "")
            if not yt_link:
                return JsonResponse({"error": "No YouTube link provided"}, status=400)

            yt_title = get_Title(yt_link)

            transcription = get_transcription(yt_link)
            if not transcription:
                return JsonResponse({"error": "Transcription failed"}, status=500)

            blog_content = generate_blog_from_transcript(transcription)
            if not blog_content:
                return JsonResponse({"error": "Blog Generation failed"}, status=500)

            # save blog content to database
            user = request.user
            youtube_title = yt_title
            youtube_link = yt_link
            generated_content = blog_content
            blog_post = BlogPost(user=user, youtube_title=youtube_title, youtube_link=youtube_link, generated_content=generated_content)
            blog_post.save()
            
            return JsonResponse({"content": blog_content})
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"error": "Internal Server Error"}, status=500)
          
    else:
        return JsonResponse({"error": "Invalid Request Method"}, status=405)


def all_blogs(request):
  blog_articles = BlogPost.objects.filter(user=request.user)
  return render(request,"../templates/all-blogs.html",{"articles":blog_articles})


def blog_details(request,pk):
  blog_article_post = BlogPost.objects.get(id = pk)
  if request.user == blog_article_post.user:
    return render(request,"blog-details.html",{'article':blog_article_post})