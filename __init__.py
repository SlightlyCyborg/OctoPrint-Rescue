import threading
import time
import os.path
import octoprint.plugin
import logging
from octoprint.printer.standard import Printer

__plugin_name__        =  "Rescue"
__plugin_version__     =  "0.1"
__plugin_description__ =  "Saves your a** when you unplug, reboot, or otherwise accidently stop a 3d print."
__plugin_author__      =  "SlightlyCyborg"
__plugin_url__         =  "https://github.com/SlightlyCyborg/OctoPrint-Rescue"


class Rescue_Plugin(octoprint.plugin.EventHandlerPlugin, octoprint.plugin.TemplatePlugin, octoprint.plugin.AssetPlugin, octoprint.plugin.SimpleApiPlugin):
    def __init__(self):
        self.active = False
        self._logger = logging.getLogger(__name__)
        self.num_gcodes_sent = -1
        self.active_lock = threading.Lock()
        self.writer_lock = threading.Lock()
        self.writer_thread = threading.Thread(target=self.writer)
        return


    def create_printer(self, components, *args, **kwargs):
        self.printer = Printer()
        return self.printer

    def cache_last_sent_gcode(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        self.active_lock.acquire()
        if(cmd != "M105" and self.active):
            self.active_lock.release()
            self.writer_lock.acquire()
            self.num_gcodes_sent += 1
            self.writer_lock.release()
        else:
            self.active_lock.release()
        return

    def construct_plugin_template(self):
        new_sidebar_file_name  = "{}/templates/Rescue_sidebar.jinja2".format(self._basefolder)
        state_source_file_name = "src/octoprint/templates/sidebar/state.jinja2"
        rescue_button_file_name = "{}/templates/button.jinja2".format(self._basefolder)

        with open(state_source_file_name, "r") as state_source_file:
            state_source = state_source_file.read()

        with open(rescue_button_file_name, "r") as rescue_button_source_file:
            rescue_button_source = rescue_button_source_file.read()

        source = "{}\n{}".format(state_source, rescue_button_source)

        with open(new_sidebar_file_name, "w") as new_sidebar_file:
            new_sidebar_file.write(source)

    def get_api_commands(self):
        return dict(
            command1=[])

    def get_assets(self):
        return dict(
            js = ["js/Rescue.js"])

    def get_template_configs(self):
        self._logger.critical("IN HERE!!!!!!!!!\n\n")
        self._logger.critical("{}".format(self._identifier))
        return [{"type":"sidebar", "template":"Rescue_sidebar.jinja2"}]

    def gen_rescue_gcode(self):
        self._logger.critical(self._printer.get_current_job())
        job = self._printer.get_current_job()
        file_name = job['file']['name']
        full_path = self._file_manager.path_on_disk(job['file']['origin'], job['file']['path'])
        self._logger.critical("Full Path: {}".format(full_path))
        if file_name is None:
            return -1

        #See if this print can be rescued!
        #potential_backup_filename = "{}/{}.bak".format(self.get_plugin_data_folder(), file_name)
        #backup_exists = os.path.isfile(potential_backup_filename)

        #if not backup_exists:
        #    return -1

        #with open(potential_backup_filename) as f:
        #    last_gcode_sent = int(f.read())
        #with open(file_name, "r") as f:
        #    gcode = f.read().splitlines()
        #    pass

    def on_api_command(self, command, data):
        import flask
        if command == "command1":
            file_path = self.gen_rescue_gcode()
            if file_path == -1:
                return flask.jsonify(error="broken")
            self._printer.select_file(file_path, False, True)
            pass

    def load_recovery_icon(self):
        pass

    def on_event(self, event, payload):
        if event == "PrintStarted":
            self._logger.critical("Started Print")
            self.print_name = payload['name']
            self.active = True
            self.writer_thread.start()
        if event == "PrintDone" or event == "PrintCancelled" or event == "PrintFailed":
            self.active_lock.acquire()
            self.active = False
            self.active_lock.release()
            self.num_gcodes_sent = 0
            self.writer_thread = threading.Thread(target=self.writer)
        return

    def writer(self):
        self.active_lock.acquire()
        while(self.active):
            self.active_lock.release()
            self.writer_lock.acquire()
            n = self.num_gcodes_sent
            self.writer_lock.release()
            print_name = 1
            filename = "{}/{}.bak".format(self.get_plugin_data_folder(), print_name)
            self._logger.critical(filename)
            with open(filename, 'w') as f:
                f.write("{}".format(n))
            time.sleep(5)
            self.active_lock.acquire()
        self.active_lock.release()



cur_gcode_command_number = 0

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = Rescue_Plugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.comm.protocol.gcode.sent": __plugin_implementation__.cache_last_sent_gcode,
    }
