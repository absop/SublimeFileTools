import sublime
import sublime_plugin

import functools
import os
import shutil
import subprocess
import threading
import traceback

from Default import send2trash


class Loger:
    debug = False
    employer = __package__

    def print(*args):
        if Loger.debug:
            print('%s:' % Loger.employer, *args)

    def error(errmsg):
        sublime.error_message(errmsg)

    def relative_path(path):
        for folder in sublime.active_window().folders():
            if path.startswith(folder):
                return path[len(os.path.dirname(folder)):]
        return path

    def threading(function, ing_msg, done_msg, on_done=None):
        def check(last_view, i, d):
            active_view = sublime.active_window().active_view()
            if last_view != active_view:
                last_view.erase_status(Loger.employer)

            if not thread.is_alive():
                cleanup = active_view.erase_status
                Loger.print(done_msg)
                active_view.set_status(Loger.employer, done_msg)
                sublime.set_timeout(lambda: cleanup(Loger.employer), 2000)
                if on_done is not None:
                    on_done()
                return

            dynamic = " [%s=%s]" % (' ' * i, ' ' * (7 - i))
            active_view.set_status(Loger.employer, ing_msg + dynamic)

            if i == 0 or i == 7:
                d = -d

            sublime.set_timeout(lambda: check(active_view, i + d, d), 100)

        Loger.print("Start " + ing_msg)
        thread = threading.Thread(target=function)
        thread.start()
        check(sublime.active_window().active_view(), 0, -1)


class OpenContextPathCommand(sublime_plugin.TextCommand):
    def run(self, edit, event):
        if os.path.isfile(self.path):
            self.view.window().open_file(self.path)
        elif os.path.isdir(self.path):
            self.view.window().run_command("open_dir", {"dir": self.path})

    def is_visible(self, event):
        return self.path is not None

    def find_path(self, event):
        view = self.view
        if view.has_non_empty_selection_region():
            selected = view.sel()[0]
            selected_content = view.substr(selected)
        else:
            pt = view.window_to_text((event["x"], event["y"]))
            selected_content = view.substr(view.extract_scope(pt))
        path = selected_content.strip('\'"')
        if os.path.exists(path):
            self.path = path
            return path
        elif view.file_name():
            dirname = os.path.dirname(view.file_name())
            file = path.lstrip('\\/')
            path = os.path.join(dirname, file)
            if file and os.path.exists(path):
                self.path = path
                return file
        return None

    def description(self, event):
        self.path = None
        file = self.find_path(event)
        if file is not None:
            if os.path.isfile(self.path):
                open_cmd = "Open File: "
            elif os.path.isdir(self.path):
                open_cmd = "Open Folder: "
            if len(file) > 56:
                file = file[0:56] + "..."
            return open_cmd + file
        return ""

    def want_event(self):
        return True


class SublimeFileToolsToggleDebugCommand(sublime_plugin.WindowCommand):
    def run(self):
        Loger.debug = not Loger.debug
        print('%s: debug: %s' %(Loger.employer,  str(Loger.debug)))
        # maybe save to settings file.


class SideBarOpenTerminalHereCommand(sublime_plugin.WindowCommand):
    def is_visible(self, paths):
        return len(paths) == 1 and os.path.exists(paths[0])

    def run(self, paths):
        directory = paths[0]
        if os.path.isfile(directory):
            directory = os.path.dirname(directory)

        if sublime.platform() == "linux":
            args = "--working-directory={}".format(directory)
            commands = ["gnome-terminal", args]
            subprocess.call(commands)


# For openning multiple files in one time,
# with shift+mouse we can select multiple files
class SideBarOpenMultFilesCommand(sublime_plugin.WindowCommand):
    def run(self, paths):
        for path in paths:
            if os.path.isfile(path):
                self.window.open_file(path)

    def is_visible(self, paths):
        if len(paths) > 1:
            for path in paths:
                if os.path.isfile(path):
                    return True
        return False


class SideBarOpenFolderCommand(sublime_plugin.WindowCommand):
    def is_visible(self, paths):
        return len(paths) == 1 and os.path.isdir(paths[0])

    def run(self, paths):
        self.window.run_command("open_dir", {"dir": paths[0]})


class SideBarPasteFilesCommand(sublime_plugin.WindowCommand):
    words = None
    enabled = False
    operation = None
    origin_paths = None
    is_running = False

    @classmethod
    def clear_after_move(cls):
        cls.words = None
        cls.enabled = False
        cls.operation = None
        cls.origin_paths = None

    @classmethod
    def move(cls, origin, target):
        def retarget_views(origin, target):
            for window in sublime.windows():
                for view in window.views():
                    path = view.file_name() or ""
                    if path.startswith(origin):
                        view.retarget(target + path[len(origin):])
        shutil.move(origin, target)
        retarget_views(origin, target)

    @classmethod
    def copy(cls, origin, target):
        if os.path.isdir(origin):
            shutil.copytree(origin, target)
        else:
            shutil.copy2(origin, target)

    @classmethod
    def _operation(cls, origin, target):
        try:
            cls.operation(origin, target)
        except:
            cls.is_running = False
            traceback.print_exc()

    @classmethod
    def paste(cls, origin, target):
        _origin = Loger.relative_path(origin)
        _target = Loger.relative_path(target)
        ing, ed = cls.words
        ing_msg = "%s %s to %s" % (ing, _origin, _target)
        done_msg = "%s is %s to %s" % (_origin, ed, _target)

        function = lambda:cls._operation(origin, target)
        Loger.threading(function, ing_msg, done_msg, cls.do_next)

    @classmethod
    def checked_paste(cls, origin, target_dir):
        def handle_new_name(new_name, skip=False, replace=False):
            target = os.path.join(target_dir, new_name)
            if os.path.exists(target):
                msg = "{}\n has existed!".format(target)
                skip = sublime.ok_cancel_dialog(msg, ok_title="skip it?")
                if not skip:
                    opt = sublime.yes_no_cancel_dialog(msg,
                        yes_title="Save with new name", no_title="Replace")

                    if opt == sublime.DIALOG_CANCEL:
                        cls.is_running = False
                        return

                    if opt == sublime.DIALOG_YES:
                        panel = sublime.active_window().show_input_panel(
                            "Input a non-exist file name",
                            new_name, handle_new_name, None, None)
                        panel.sel().clear()
                        panel.sel().add(sublime.Region(0, len(new_name)))
                        return

                    skip = target == origin
                    replace = not skip
            if skip:
                cls.do_next()
            elif os.path.exists(origin):
                if replace:
                    _target = Loger.relative_path(target)
                    try:
                        Loger.print("Trying to remove: " + _target)
                        send2trash.send2trash(target)
                        Loger.print("Successful removing: " + _target)
                    except:
                        Loger.error("Failed to remove: " + _target)
                        cls.is_running = False
                        return
                cls.paste(origin, target)
            else:
                Loger.error("No such file or directory: " + origin)

        handle_new_name(os.path.basename(origin))

    @classmethod
    def do_next(cls):
        if cls.index < len(cls.origin_paths) and cls.is_running:
            path = cls.origin_paths[cls.index]
            cls.index += 1
            cls.checked_paste(path, cls.target_dir)
        else:
            if cls.operation == cls.move:
                cls.clear_after_move()
            cls.is_running = False

    def run(self, paths):
        target_dir = paths[0]
        if os.path.isfile(target_dir):
            target_dir = os.path.dirname(path)

        SideBarPasteFilesCommand.target_dir = target_dir
        SideBarPasteFilesCommand.index = 0
        SideBarPasteFilesCommand.is_running = True
        SideBarPasteFilesCommand.do_next()

    def is_visible(self, paths):
        if len(paths) == 1 and self.enabled is True:
            if os.path.exists(paths[0]):
                return True
            else:
                msg = "No such file or directory: " + paths[0]
                sublime.status_message(msg)
        return False

    def is_enabled(self, paths):
        if self.is_visible(paths):
            dirname = os.path.dirname(paths[0])
            for path in self.origin_paths:
                if dirname.startswith(path) or paths[0] == path:
                    return False
            return True
        return False


class SideBarCopyFilesCommand(sublime_plugin.WindowCommand):
    words = ("Copying", "copyed")
    operation = SideBarPasteFilesCommand.copy

    def run(self, paths):
        paths = [p for p in paths if os.path.exists(p)]
        SideBarPasteFilesCommand.words = self.words
        SideBarPasteFilesCommand.operation = self.operation
        SideBarPasteFilesCommand.origin_paths = paths
        SideBarPasteFilesCommand.enabled = True

    def is_visible(self, paths):
        if SideBarPasteFilesCommand.is_running == True:
            return False
        return len(paths) > 0 and os.path.exists(paths[0])

    def is_enabled(self, paths):
        if self.is_visible(paths):
            for i in range(len(paths)):
                for j in range(i + 1, len(paths)):
                    pi, pj = paths[i], paths[j]
                    if (os.path.dirname(pj).startswith(pi) or
                        os.path.dirname(pi).startswith(pj)):
                        return False
            return True
        return False


class SideBarMoveFilesCommand(SideBarCopyFilesCommand):
    words = ("Moving", "moved")
    operation = SideBarPasteFilesCommand.move



""": Tab bar commands
"""
class TabBarCommand(sublime_plugin.WindowCommand):
    def is_visible(self, group, index):
        self.view = self.window.views_in_group(group)[index]
        self.path = self.view.file_name()
        return self.path is not None and os.path.exists(self.path)

    def is_enabled(self, group, index):
        return self.is_visible(group, index)


class TabBarCopyFileNameCommand(sublime_plugin.WindowCommand):
    def run(self, group, index):
        branch, leaf = os.path.split(self.path)
        sublime.set_clipboard(leaf)

    def is_visible(self, group, index):
        view = self.window.views_in_group(group)[index]
        self.path = view.file_name()
        return self.path is not None


class TabBarNewFileCommand(TabBarCommand):
    def run(self, group, index):
        branch, leaf = os.path.split(self.path)
        v = self.window.show_input_panel(
            "File Name",
            leaf,
            functools.partial(self.on_done, branch),
            None, None)
        v.sel().clear()
        v.sel().add(sublime.Region(0, len(os.path.splitext(leaf)[0])))

    def on_done(self, dir, name):
        open(os.path.join(dir, name), "a").close()
        self.window.open_file(os.path.join(dir, name))


class TabBarCopyFilePathCommand(TabBarCommand):
    def is_visible(self, group, index):
        self.view = self.window.views_in_group(group)[index]
        self.path = self.view.file_name()
        return self.path is not None

    def run(self, group, index):
        sublime.set_clipboard(self.path)


class TabBarOpenContainedFolderCommand(TabBarCommand):
    def run(self, group, index):
        branch, leaf = os.path.split(self.path)
        self.window.run_command("open_dir", {"dir": branch, "file": leaf})


class TabBarSaveFileCommand(TabBarCommand):
    def run(self, group, index):
        dir = os.path.dirname(self.path)
        if not os.path.exists(dir):
            os.makedirs(dir)
        self.view.run_command("save")

    def is_visible(self, group, index):
        self.view = self.window.views_in_group(group)[index]
        self.path = self.view.file_name()
        if self.path is None:
            return False
        return not os.path.exists(self.path) or self.view.is_dirty()


class TabBarRenameFileCommand(TabBarCommand):
    def run(self, group, index):
        self.window.run_command("rename_path", {"paths": [self.path]})


class TabBarDeleteFileCommand(TabBarCommand):
    def run(self, group, index):
        name = os.path.basename(self.path).center(64)
        delete = sublime.ok_cancel_dialog(
            "Are you sure you want to delete?\n\n" + name,
            "Delete")

        if delete and self.view.close():
            import Default.send2trash as send2trash
            try:
                send2trash.send2trash(self.path)
            except:
                msg = "Unable to delete file: " + self.path
                sublime.status_message(msg)


class TabBarMoveFileCommand(TabBarCommand):
    def run(self, group, index):
        self.window.run_command("side_bar_move_files", {"paths": [self.path]})


class TabBarCopyFileCommand(TabBarCommand):
    def run(self, group, index):
        self.window.run_command("side_bar_copy_files", {"paths": [self.path]})


class TabBarCloneFileCommand(TabBarCommand):
    def run(self, group, index):
        path, ext = os.path.splitext(self.path)
        number = 1
        if path:
            while path[-number].isdecimal():
                number += 1

            if number > 1:
                cut = 1 - number
                path, number = path[:cut], int(path[cut:])

        while os.path.exists(path + str(number) + ext):
            number += 1
        path += str(number) + ext

        shutil.copy(self.path, path)
        self.window.open_file(path)
