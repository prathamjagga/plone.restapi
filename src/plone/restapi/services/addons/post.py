from plone.restapi.services import Service
from plone.restapi.services.addons.addons import Addons
from zope.component import getMultiAdapter
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse

import logging
import plone


logger = logging.getLogger("Plone")


@implementer(IPublishTraverse)
class AddonsPost(Service):
    """Performs install/upgrade/uninstall functions on an addon."""

    def __init__(self, context, request):
        super().__init__(context, request)
        self.params = []
        self.errors = {}
        self.addons = Addons(context, request)

    def publishTraverse(self, request, name):
        # Consume any path segments after /@addons as parameters
        self.params.append(name)
        return self

    def reply(self):
        # Unpack taking into account that third argument might not be present
        addon, action, profile = (self.params + [None] * 3)[:3]

        # Disable CSRF protection
        if "IDisableCSRFProtection" in dir(plone.protect.interfaces):
            alsoProvides(self.request, plone.protect.interfaces.IDisableCSRFProtection)

        if action == "install":
            result = self.addons.install_product(addon)
        elif action == "uninstall":
            result = self.addons.uninstall_product(addon)
        elif action == "upgrade":
            result = self.addons.upgrade_product(addon)
        elif action == "import":
            result = self.addons.import_profile(addon, profile)
        else:
            raise Exception(f"Unknown action {action}")

        prefer = self.request.getHeader("Prefer")
        if prefer == "return=representation":
            control_panel = getMultiAdapter(
                (self.context, self.request), name="prefs_install_products_form"
            )
            all_addons = control_panel.get_addons()

            result = {"items": {"@id": f"{self.context.absolute_url()}/@addons"}}
            addons_data = []
            for a in all_addons.values():
                addons_data.append(self.addons.serializeAddon(a))
            result["items"] = addons_data

            self.request.response.setStatus(200)
            return result
        self.request.response.setStatus(204)
