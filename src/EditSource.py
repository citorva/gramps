#! /usr/bin/python -O
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000  Donald N. Allingham
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
import os
import string
import utils

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
from gtk import *
from gnome.ui import *
import gnome.mime

import libglade

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import intl
import const
import utils
import Config
from RelLib import *
import RelImage

_ = intl.gettext

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
INDEX  = "i"
SOURCE = "s"

class EditSource:

    def __init__(self,source,db,func):
        self.source = source
        self.db = db
        self.callback = func
        self.path = db.getSavePath()
        self.not_loaded = 1

        self.selectedIcon = -1
        self.currentImages = []
        self.top_window = libglade.GladeXML(const.gladeFile,"sourceEditor")
        self.title = self.top_window.get_widget("source_title")
        self.author = self.top_window.get_widget("author")
        self.pubinfo = self.top_window.get_widget("pubinfo")
        self.note = self.top_window.get_widget("source_note")

        self.title.set_text(source.getTitle())
        self.author.set_text(source.getAuthor())
        self.pubinfo.set_text(source.getPubInfo())

        self.note.set_point(0)
        self.note.insert_defaults(source.getNote())
        self.note.set_word_wrap(1)

        self.photo_list = self.top_window.get_widget("photolist")

        self.top_window.signal_autoconnect({
            "destroy_passed_object" : utils.destroy_passed_object,
            "on_photolist_select_icon" : on_photo_select_icon,
            "on_photolist_button_press_event" : on_photolist_button_press_event,
            "on_switch_page" : on_switch_page,
            "on_addphoto_clicked" : on_add_photo_clicked,
            "on_deletephoto_clicked" : on_delete_photo_clicked,
            "on_sourceapply_clicked" : on_source_apply_clicked
            })

        self.top = self.top_window.get_widget("sourceEditor")
        self.top.set_data(SOURCE,self)

        if self.source.getId() == -1:
            self.top_window.get_widget("add_photo").set_sensitive(0)
            self.top_window.get_widget("delete_photo").set_sensitive(0)

    #-------------------------------------------------------------------------
    #
    # add_thumbnail - Scale the image and add it to the IconList. 
    #
    #-------------------------------------------------------------------------
    def add_thumbnail(self,photo):
        src = photo.getPath()
        thumb = self.db.getSavePath() + os.sep + ".thumb" + os.sep + \
                os.path.basename(src)

        RelImage.check_thumb(src,thumb,const.thumbScale)

        self.photo_list.append(thumb,photo.getDescription())
        
    #-------------------------------------------------------------------------
    #
    # load_images - clears the currentImages list to free up any cached 
    # Imlibs.  Then add each photo in the source's list of photos to the 
    # photolist window.
    #
    #-------------------------------------------------------------------------
    def load_images(self):
        if len(self.source.getPhotoList()) == 0:
            return
        self.photo_list.freeze()
        self.photo_list.clear()
        for photo in self.source.getPhotoList():
            self.add_thumbnail(photo)
        self.photo_list.thaw()

#-----------------------------------------------------------------------------
#
#
#
#-----------------------------------------------------------------------------
def on_source_apply_clicked(obj):

    edit = obj.get_data(SOURCE)
    title = edit.title.get_text()
    author = edit.author.get_text()
    pubinfo = edit.pubinfo.get_text()
    note = edit.note.get_chars(0,-1)
    
    if author != edit.source.getAuthor():
        edit.source.setAuthor(author)
        utils.modified()
        
    if title != edit.source.getTitle():
        edit.source.setTitle(title)
        utils.modified()
        
    if pubinfo != edit.source.getPubInfo():
        edit.source.setPubInfo(pubinfo)
        utils.modified()
        
    if note != edit.source.getNote():
        edit.source.setNote(note)
        utils.modified()

    utils.destroy_passed_object(edit.top)
    edit.callback(edit.source)

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def on_switch_page(obj,a,page):
    src = obj.get_data(SOURCE)
    if page == 2 and src.not_loaded:
        src.not_loaded = 0
        src.load_images()

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def on_photo_select_icon(obj,iconNumber,event):
    obj.get_data(SOURCE).selectedIcon = iconNumber

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def on_delete_photo_clicked(obj):
    edit_source_obj = obj.get_data(SOURCE)
    icon = edit_source_obj.selectedIcon

    if icon == -1:
        return
    
    photolist = edit_source_obj.source.getPhotoList()
    edit_source_obj.photo_list.remove(icon)
    del photolist[edit_source_obj.selectedIcon]

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def on_add_photo_clicked(obj):

    edit_source = obj.get_data(SOURCE)
    
    image_select = libglade.GladeXML(const.imageselFile,"imageSelect")

    edit_source.isel = image_select

    image_select.signal_autoconnect({
        "on_savephoto_clicked" : on_savephoto_clicked,
        "on_name_changed" : on_name_changed,
        "destroy_passed_object" : utils.destroy_passed_object
        })

    edit_source.fname = image_select.get_widget("fname")
    edit_source.add_image = image_select.get_widget("image")
    edit_source.external = image_select.get_widget("private")
    image_select.get_widget("imageSelect").set_data(SOURCE,edit_source)
    image_select.get_widget("imageSelect").show()

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def on_savephoto_clicked(obj):
    edit_source_obj = obj.get_data(SOURCE)
    image_select = edit_source_obj.isel
    
    filename = image_select.get_widget("photosel").get_full_path(0)
    description = image_select.get_widget("photoDescription").get_text()

    if os.path.exists(filename) == 0:
        return

    prefix = "s" + str(edit_source_obj.source.getId())
    if edit_source_obj.external.get_active() == 1:
        if os.path.isfile(filename):
            name = filename
        else:
            return
    else:
        name = RelImage.import_photo(filename,edit_source_obj.path,prefix)
        if name == None:
            return
        
    photo = Photo()
    photo.setPath(name)
    photo.setDescription(description)
    
    edit_source_obj.source.addPhoto(photo)
    edit_source_obj.add_thumbnail(photo)

    utils.modified()
    utils.destroy_passed_object(obj)

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def on_photolist_button_press_event(obj,event):

    myobj = obj.get_data(SOURCE)
    icon = myobj.selectedIcon
    if icon == -1:
        return
    
    if event.button == 3:
        photo = myobj.source.getPhotoList()[icon]
        menu = GtkMenu()
        item = GtkTearoffMenuItem()
        item.show()
        view = GtkMenuItem(_("View Image"))
        view.set_data("m",myobj)
        view.connect("activate",on_view_photo)
        view.show()
        edit = GtkMenuItem(_("Edit Image"))
        edit.set_data("m",myobj)
        edit.connect("activate",on_edit_photo)
        edit.show()
        change = GtkMenuItem(_("Edit Description"))
        change.set_data("m",myobj)
        change.connect("activate",on_change_description)
        change.show()
        menu.append(item)
        menu.append(view)
        menu.append(edit)
        menu.append(change)
        if photo.getPrivate() == 0:
            private = GtkMenuItem(_("Convert to private copy"))
            private.set_data("m",myobj)
            private.connect("activate",on_convert_to_private)
            private.show()
            menu.append(private)
        menu.popup(None,None,None,0,0)

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def on_convert_to_private(obj):
    edit_source_obj = obj.get_data("m")
    photo = edit_source_obj.source.getPhotoList()[edit_source_obj.selectedIcon]

    prefix = "i" + str(edit_source_obj.source.getId())
    name = RelImage.import_photo(photo.getPath(),edit_source_obj.path,prefix)

    photo.setPath(name)
    photo.setPrivate(1)

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def on_view_photo(obj):
    myobj = obj.get_data("m")
    photo = myobj.source.getPhotoList()[myobj.selectedIcon]
    type = gnome.mime.type(photo.getPath())
    
    prog = string.split(gnome.mime.get_value(type,'view'))
    args = []
    for val in prog:
        if val == "%f":
            args.append(photo.getPath())
        else:
            args.append(val)
    
    if os.fork() == 0:
        os.execvp(args[0],args)

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def on_edit_photo(obj):
    myobj = obj.get_data("m")
    photo = myobj.source.getPhotoList()[myobj.selectedIcon]
    if os.fork() == 0:
        os.execvp(const.editor,[const.editor, photo.getPath()])

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def on_change_description(obj):
    myobj = obj.get_data("m")
    photo = myobj.source.getPhotoList()[myobj.selectedIcon]
    window = libglade.GladeXML(const.imageselFile,"dialog1")

    text = window.get_widget("text")
    text.set_text(photo.getDescription())

    image2 = RelImage.scale_image(photo.getPath(),200.0)
    window.get_widget("photo").load_imlib(image2)
    window.get_widget("dialog1").set_data("p",photo)
    window.get_widget("dialog1").set_data("t",text)
    window.get_widget("dialog1").set_data("m",obj.get_data("m"))
    window.signal_autoconnect({
        "on_cancel_clicked" : utils.destroy_passed_object,
        "on_ok_clicked" : on_ok_clicked,
        "on_apply_clicked" : on_apply_clicked
        })

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def on_name_changed(obj):
    edit_person = obj.get_data(SOURCE)
    file = edit_person.fname.get_text()
    if os.path.isfile(file):
        image = RelImage.scale_image(file,const.thumbScale)
        edit_person.add_image.load_imlib(image)
