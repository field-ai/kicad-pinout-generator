#!/usr/bin/env python

import os
import wx

import pcbnew

from . import connector
from . import pinout_generator_result

SELECTOR = {
    'wireviz':0
}

class PinoutDialog(pinout_generator_result.PinoutDialog):
    def onDeleteClick(self, _):
        return self.EndModal(wx.ID_DELETE)

class PinoutGenerator(pcbnew.ActionPlugin):

    def defaults(self):
        self.name = "Pinout Generator"
        self.category = "Read PCB"
        self.description = "Generates pinout exports from the PCB nets"
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(os.path.dirname(__file__), 'logo.png')

    def set_output(self):

        components = [connector.make_connector(component) for component in self.footprint_selection]
        output = connector.wireviz_format(components)
        self.set_result(output)
        

    def Run(self):
        # Look for selected FP
        self.footprint_selection = [
            footprint
            for footprint in pcbnew.GetBoard().GetFootprints()
            if footprint.IsSelected()
        ]

        # Check selection len
        if not self.footprint_selection:
            wx.MessageBox("Select at least one component!")
            return

        # WX setup
        dialog = PinoutDialog(None)

        # wx form controls
        self.set_result = dialog.result.SetValue
        self.enable_cb = dialog.pinNameCB.Enable
        self.is_pinname_not_number = dialog.pinNameCB.GetValue
        self.get_pin_name_filter = dialog.pinNameFilter.GetValue
        self.enable_filter = dialog.pinNameFilter.Enable

        # Init output
        self.set_output()
        
        modal_result = dialog.ShowModal()
        dialog.Destroy()
