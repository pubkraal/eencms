import logging

from pylons import request, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from cms.lib.exceptions import NotFoundException
from cms.lib.base import BaseController, render, Session
from cms.lib.decorators import get, post, access_cmsuser, access_all
import cms.model as model

log = logging.getLogger(__name__)


class PageController(BaseController):
    @get
    @access_all
    def index(self):
        return render('/pages/reference/index.html')

    @get
    @access_all
    def view(self, id=None, title=None):
        try:
            c.page = c.tree.find_node(id=int(id))
        except NotFoundException:
            abort(404)
        except:
            raise
        if not c.page.type == 'content':
            abort(404)

        return render('/pages/page/view.html')

    @get
    @access_cmsuser
    def edit(self, id=None):
        if id == 'new':
            c.page = model.Page()
            c.page.id = 'new'
        else:
            c.page = c.tree.find_node(int(id))
        return render('/pages/page/edit.html')

    @post
    @access_cmsuser
    def submit(self, id=None):
        rp = request.POST
        c.page = c.tree.find_node(id=int(id))
        try:
            content = Session.query(model.Content).get(c.page.content_id)
        except:
            content = model.Content()

        c.page.title = rp.get('title')
        content.content = rp.get('content')
        c.page.menutitle = rp.get('menutitle')
        if not content.id:
            Session.add(content)
        Session.commit()
        c.page.type = 'content'
        c.page.content_id = content.id
        Session.commit()

        return redirect(url(controller='page',
                            action='view',
                            id=c.page.id,
                            title=c.page.get_url_title()))

    @post
    @access_cmsuser
    def addbelow(self, id=None):
        sibling = c.tree.find_node(int(id))
        newid = c.tree.add_child(sibling.parent_id, sibling.id)
        return redirect(url(controller='page', action='edit', id=newid))

    @post
    @access_cmsuser
    def moveup(self, id=None):
        c.tree.move_node(int(id), 'up')
        node = c.tree.find_node(int(id))
        return redirect(node.get_url())

    @post
    @access_cmsuser
    def movedown(self, id=None):
        c.tree.move_node(int(id), 'down')
        node = c.tree.find_node(int(id))
        return redirect(node.get_url())

    @post
    @access_cmsuser
    def delete(self, id=None):
        node = c.tree.find_node(int(id))
        parent_id = node.parent_id
        try:
            if node.type == 'content':
                content = Session.query(model.Content).get(node.content_id)
                Session.delete(content)
        except:
            pass
        c.tree.del_child(node.id)

        childnodes = c.tree.get_nodes(parent_id)
        if len(childnodes) < 1:
            return redirect(url(controller='home', action='index'))
        else:
            firstsub = childnodes[0]
            return redirect(firstsub.get_url())
