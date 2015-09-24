#!/usr/bin/env python
#coding=utf8

import logging
from tornado.web import HTTPError
from handler import BaseHandler
from lib.route import route
from model import Oauth, User, UserVcode, Page, Apply, Shop, Ad

@route(r'/', name='index') #首页
class IndexHandler(BaseHandler):
    def get(self):
        oauth = None
        if 'oauth' in self.session:
            oauth = self.session['oauth']
	user=self.get_current_user()
        if user:
            url="/signup?sharer="+user.mobile
            self.redirect(url,permanent=True)
	else:
            self.render("site/signup.html", oauth = oauth)    

@route(r'/apply', name='apply') #集团购买/会员特惠
class ApplyHandler(BaseHandler):
    
    def get(self):
        self.render("site/apply.html")
    
    def post(self):
        coname = self.get_argument("coname", None)
        city = self.get_argument("city", None)
        region = self.get_argument("region", None)
        address = self.get_argument("address", None)
        try:
            pnumber = int(self.get_argument("pnumber", 1))
        except:
            pnumber = 1
        name = self.get_argument("name", None)
        tel = self.get_argument("tel", None)
        mobile = self.get_argument("mobile", "")
        
        applyed = Apply()
        applyed.coname = coname
        applyed.city= city
        applyed.region = region
        applyed.address = address
        applyed.pnumber = pnumber
        applyed.name = name
        applyed.tel = tel
        applyed.mobile = mobile
        
        try:
            applyed.validate()
            applyed.save()
            self.flash("申请成功，请等待我们的消息。", "ok")
            self.redirect("/apply")
            return
        
        except Exception, ex:
            self.flash(str(ex))
        
        self.render("site/apply.html")

@route(r'/signin', name='signin') #登录
class SignInHandler(BaseHandler):
    
    def get(self):
	user=self.get_current_user()
        if user:
	    url="/signup?sharer="+user.mobile
            self.redirect(url,permanent=True)
            return
        
        oauth = None
        if 'oauth' in self.session:
            oauth = self.session['oauth']
        
        self.render("site/signin.html", oauth = oauth, next = self.next_url)
    
    def post(self):
        if self.get_current_user():
            self.redirect("/")
            return
        
        mobile = self.get_argument("mobile", None)
        password = self.get_argument("password", None)
        
        if mobile and password:
            try:
                user = User.get(User.mobile == mobile)
                
                if user.check_password(password):
                    if user.group > 0:
                        user.updatesignin()
                        
                        self.session['user'] = user
                        
                        if 'oauth' in self.session:
                            oauth = self.session['oauth']
                            
                            o = Oauth()
                            o.uid = user.id
                            o.openid = oauth['id']
                            o.src = oauth['src']
                            o.save()
                            
                            del self.session['oauth']
                        
                        self.session.save()
			if mobile != "root":
                        	url="/signup?sharer="+user.mobile
            			self.redirect(url,permanent=True)
			else:
				self.redirect("/admin/users")
		        return
                    else:
                        self.flash("此账户被禁止登录，请联系管理员。")
                else:
                    self.flash("密码错误")
            except Exception, ex:
                logging.error(ex)
                self.flash("此用户不存在")
        else:
            self.flash("请输入用户名或者密码")
        
        self.render("site/signin.html", next = self.next_url)

@route(r'/signup', name='signup') #注册
class SignUpHandler(BaseHandler):
    
    def get(self):
	user=self.get_current_user()
        sharer = self.get_argument("sharer", None)
	if user:
            url="/signup?sharer="+user.mobile
            if sharer == None:
		self.redirect(url,permanent=True)
            else:
		self.render("site/share.html" , user = user, mobile=user.mobile)
	    return
      
        oauth = None
        if 'oauth' in self.session:
            oauth = self.session['oauth']
	sharer = self.get_argument("sharer", None)
        self.render("site/signup.html", oauth = oauth, sharer = sharer)
    
    def post(self):
        #if self.get_current_user():
         #   self.redirect("/")
         #   return
        
        mobile = self.get_argument("mobile", None)
        password = self.get_argument("password", None)
        apassword = self.get_argument("apassword", None)
        vcode = self.get_argument("vcode", None)
        sharer = self.get_argument("sharer", None)
        realname=self.get_argument("realname",None) 
        
        user = User()
        user.mobile = mobile
	user.realname = realname
        user.password = User.create_password(password)
        
        try:
            user.validate()
            
            if password and apassword:
                if len(password) < 6:
                    self.flash("请确认输入6位以上新密码")
                elif password != apassword:
                    self.flash("请确认新密码和重复密码一致")
		elif len(realname) > 32:
		    self.flash("微信账号超出长度限制")
		elif len(realname) < 2:
		    self.flash("微信账号太短")
                else:
                    #if UserVcode.select().where((UserVcode.mobile == mobile) & (UserVcode.vcode == vcode)).count() > 0:
                    #    UserVcode.delete().where((UserVcode.mobile == mobile) & (UserVcode.vcode == vcode)).execute()
                        user.save()
       			user.updatesignin()
                        self.session['user'] = user
                 
                        if 'oauth' in self.session:
                            oauth = self.session['oauth']
                            o = Oauth()
                            o.uid = user.id
                            o.openid = oauth['id']
                            o.src = oauth['src']
                            o.save()
                            
                            del self.session['oauth']
                            self.session.save()
                        User.update(credit = User.credit + 1).where(User.mobile == mobile).execute()
                        #if sharer != None
                        User.update(credit = User.credit + 1).where(User.mobile == sharer).execute()
                        self.flash("注册成功，请先登录。", "ok")
                        url="/signup?sharer="+user.mobile
            		self.redirect(url,permanent=True)
			return
                    #else:
                    #    self.flash("请输入正确的验证码")
            else:
                self.flash("请输入密码和确认密码")
        except Exception, ex:
            self.flash(str(ex))
        self.render("site/signup.html")

@route(r'/signout', name='signout') #退出
class SignOutHandler(BaseHandler):
    
    def get(self):
        if "user" in self.session:
            del self.session["user"]
            self.session.save()
        self.redirect(self.next_url)

@route(r'/resetpassword', name='resetpassword') #忘记密码
class ResetPasswordHandler(BaseHandler):
    
    def get(self):
        if self.get_current_user():
            self.redirect("/")
            return
        
        self.render("site/resetpassword.html")
        
    def post(self):
        #if self.get_current_user():
         #   self.redirect("/")
          #  return
        
        mobile = self.get_argument("mobile", None)
        password = self.get_argument("password", None)
        apassword = self.get_argument("apassword", None)
        vcode = self.get_argument("vcode", None)
        
        try:
            user = User().get(mobile = mobile)
        except:
            self.flash("此用户不存在")
            self.redirect("/resetpassword")
            return
        
        try:
            if password and apassword:
                if len(password) < 6:
                    self.flash("请确认输入6位以上新密码")
                elif password != apassword:
                    self.flash("请确认新密码和重复密码一致")
                else:
                    if UserVcode.select().where((UserVcode.mobile == mobile) & (UserVcode.vcode == vcode)).count() > 0:
                        UserVcode.delete().where((UserVcode.mobile == mobile) & (UserVcode.vcode == vcode)).execute()
                        user.password = User.create_password(password)
                        user.save()
                        self.flash("重置密码成功，请先登录。", "ok")
                        self.redirect("/signin")
                        return
                    else:
                        self.flash("请输入正确的验证码")
            else:
                self.flash("请输入密码和确认密码")
        except Exception, ex:
            self.flash(str(ex))
        
        self.render("site/resetpassword.html")

@route(r'/p/([^/]+)', name='staticpage') #栏目页
class StaticPageHandler(BaseHandler):
    
    def get(self, slug):
        try:
            page = Page.get(slug = slug)
        except:
            raise HTTPError(404)
            return
        
        self.render("static/%s" % page.template, page = page)
