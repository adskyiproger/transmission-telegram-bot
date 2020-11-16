from models.SearchNonameClub import SearchNonameClub
from telegram import InlineKeyboardButton 
from models.SearchRUTOR import SearchRUTOR
from models.SearchEZTV import SearchEZTV
from models.SearchKAT import SearchKAT
import hashlib

class SearchTorrents:
     CLASSES={ "nnmclub" : SearchNonameClub,
               "rutor" : SearchRUTOR,
               "EZTV" : SearchEZTV,
               "KAT" : SearchKAT
             }
     CACHE={}
     def __init__(self, name="rutor", search_string="test"):
         self.KEYBOARD=[]
         self.PAGES={}
         self.LINKS={}
         self.POSTS={}
         x=search_string
         print("Name {0} with {1}".format(name,search_string))
         srch_hash=hashlib.md5(str(name+search_string).encode('utf-8')).hexdigest()
         if srch_hash in self.CACHE.keys():
             print("Using value from cache")
             self.POSTS=self.CACHE[srch_hash]
         else:
             TRACKER=self.CLASSES[name]()
             TRACKER.search(x)
             self.POSTS=TRACKER.POSTS
             self.CACHE[srch_hash]=TRACKER.POSTS

         n_posts=len(self.POSTS)
         n_pages=0
         if n_posts > 0 and n_posts > 5:
              n_pages=n_posts//5
              if n_posts % 5 > 0:
                  n_pages+=1
         print("Pages: {0}, Posts: {1}".format(n_pages,n_posts))
        
         for jj in range(1,n_pages+1):
             self.KEYBOARD.append(InlineKeyboardButton(str(jj),callback_data=str(jj)))

         _message=""
         kk=1
         ii=1
         jj=1
         for post in self.POSTS:
             _message=_message+"\n<b>{0}</b>: {3}  {4}\n<a href='{1}'>Info</a>     [ ▼ /download_{2} ]\n".format(post['title'],post['info'],ii,post['size'],post['date'])
             self.LINKS[str(ii)]=post['dl']
             ii+=1
             if kk == 5:
                self.PAGES[str(jj)]=_message
                kk=0
                jj+=1
                _message=""
             kk+=1
         if kk>1:
            self.PAGES[str(jj)]=_message
             
         
     
