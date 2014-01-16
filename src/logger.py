from google.appengine.ext import ndb
import webapp2
from google.appengine.runtime.apiproxy_errors import CapabilityDisabledError 
import os
import string
from google.appengine.api import xmpp
import httpagentparser
import urlparse

class LogErr(ndb.Model):
        serverName = ndb.StringProperty()
        serverPath = ndb.StringProperty()
        fileLoc = ndb.StringProperty()
        lineNo = ndb.StringProperty()
        errMsg = ndb.StringProperty()
        infoMsg = ndb.StringProperty()
        IP = ndb.StringProperty()
        UA = ndb.StringProperty()
        OSName = ndb.StringProperty()
        OSVer = ndb.StringProperty()
        BrowserName = ndb.StringProperty()
        BrowserVer = ndb.StringProperty()
        guid = ndb.StringProperty()
        ts = ndb.DateTimeProperty( auto_now_add=True )

class LogUser(ndb.Model):
        userName = ndb.StringProperty()
        serverName = ndb.StringProperty()
        userActive = ndb.BooleanProperty(default=False)
        
class MainHandler(webapp2.RequestHandler):
    def get(self):
        QfileLoc = self.request.get("fl")
        QlineNo = self.request.get("ln")
        QerrMsg = self.request.get("err")
        QinfoMsg = self.request.get("info")
        QUA = os.environ['HTTP_USER_AGENT']
        try:
            QOSName = httpagentparser.detect(QUA)['os']['name']
        except:
            QOSName = "Unknown"
        try:
            QOSVer = httpagentparser.detect(QUA)['os']['version']
        except:
            QOSVer = "Unknown"
        try:
            QBrowserName = httpagentparser.detect(QUA)['browser']['name']
        except:
            QBrowserName = "Unknown"
        try:
            QBrowserVer = httpagentparser.detect(QUA)['browser']['version']
        except:
            QBrowserVer = "Unknown"
        QIP = os.environ['REMOTE_ADDR']
        o = urlparse.urlsplit(self.request.get("sn"))
        QserverName = o.scheme + "://" + o.netloc
        QserverPath = o.path
        if o.query != "":
            QserverPath += "?" + o.query
        if o.fragment != "":
            QserverPath += "#" + o.fragment
        Qguid = self.request.get("ui")
        Qi = self.request.get("i")
        storeLog = LogErr(serverName=QserverName, serverPath=QserverPath, fileLoc=QfileLoc, lineNo=QlineNo, errMsg=QerrMsg, infoMsg=QinfoMsg, IP=QIP, UA=QUA, OSName=QOSName, OSVer=QOSVer, BrowserName=QBrowserName, BrowserVer=QBrowserVer, guid=Qguid)
        try:
            storeLog.put()
            errMsg = ""
        except CapabilityDisabledError as err:
            errMsg = "// AppEngine is in read-only mode at the moment: " + err + "\n"
        except Exception as err: 
            # fail gracefully if insert fails
            errMsg = "// Insert failed: " + err + "\n"
            pass
            
        self.response.out.write("jsErrLog.removeScript(" + Qi + ") // jsErrRpt\n")
        if errMsg !="":
            self.response.out.write(errMsg)
            
        q = ndb.gql("SELECT * FROM LogUser " + 
            "WHERE serverName = :1 AND userActive = True", 
            string.lower(QserverName)) 
        results = q.get() 
        if results != None:
            # Send alert via XMPP/GTalk
            chat_message_sent = False
            user_address = results.userName
            if xmpp.get_presence(user_address):
                msg = ("An error was just reported for " + QserverName + " at line " + QlineNo + " in " + QfileLoc + ".\nVisit http://jsErrLog.appspot.com/report.html?sn=" + QserverName + " for more details.")
                status_code = xmpp.send_message(user_address, msg)
                chat_message_sent = (status_code == xmpp.NO_ERROR)
                

application = webapp2.WSGIApplication([('/logger.js', MainHandler)],
                                     debug=True)
