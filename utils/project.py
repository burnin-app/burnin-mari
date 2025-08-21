import mari


def isProjectSuitable():
    if mari.projects.current() is None:
        mari.utils.message("Please open a project before exporting channels.")
        return False
        
    geo = mari.geo.current()
    if geo is None:
        mari.utils.message("Please select an object to export layers from.")
        return False

    chan = geo.currentChannel()
    if chan is None:
        mari.utils.message("Please select a channel to export layers from.")
        return False

    return True
