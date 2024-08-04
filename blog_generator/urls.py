from django.urls import path
from . import views

urlpatterns =[
  path("",views.index,name = "index"),
  path("login",views.login_page,name = "login"),
  path("signup",views.signup_page,name = "signup"),
  path("logout",views.logout_page,name = "logout"),
  path("all-blogs",views.all_blogs,name = "all-blogs"),
  path("generate_blogs",views.generate_blogs,name = "generate-blogs"),
  path("blog-details/<int:pk>/",views.blog_details,name="blog-details")
  
]