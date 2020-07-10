![License][license-image]


# SuperMenus
The package contain a set of functions that will make you use `Sublime Text` more conveniently, these functions can be classified into three kinds: `View Context`, `Side Bar` and `Tab Bar`.


## View Context

### SidebarFileManager
#### Translator
A extensible translator, default by [youdao](http://fanyi.youdao.com/)

![translator youdao](images/youdao.png)

##### How to use?
As a example, select the words `Hello World`(in Sublime Text) and right click, you will get clickable menus to choose to translate it. If you right click without selecting, you will also get the menus of translator when you had inserted the cursor into a word.

#### Search Online
Select a paragraph and search it online.
You can add more context menus to have more platforms to choose, just by adding platform settings with it's url in the settings file.
**Example**:
If your settings file contain the following settings:
```json
"platforms": {
    "Wiki": "https://en.wikipedia.org/wiki/%s",
    "Github": "https://github.com/search?q=%s&type=Code",
    "Baidu": "https://www.baidu.com/s?ie=UTF-8&wd=%s",
    // "Google" : "http://google.com/#q=%s",
}
```
you will get three chioce:
![search online](images/search3.png)

And if your settings file contain settings like this:
```json
"platforms": {
    "Wiki": "https://en.wikipedia.org/wiki/%s",
    "Github": "https://github.com/search?q=%s&type=Code",
    "Baidu": "https://www.baidu.com/s?ie=UTF-8&wd=%s",
    "Google" : "http://google.com/#q=%s",
}
```
you will get four items:
![search online](images/search4.png)

#### Open Other Files
Right click, you can open other files under the folder of current file list under a menu item named `Open Other Files`.
​    ![](images/open.png)


## Side Bar
- Count lines of code(it will ask you to input the extensions of files you want) under a directory mounted on the side bar. when you have input a series of extensions, it count each file under the directory and its subdirectory whose extensions in you input set and finally show you the statistical result in a view like this:
    ![code lines](images/lines.png)
    double click the path, and you will open the file.

- Get the size information of a folder, shown in output panel.
    ![file size](images/filesize.png)

- `Copy`, `Move` files or folders(have mounted on sublime's side bar) and paste into a folder have mounted on sublime's side bar.
    you can choose more than one files in one time, use the host key `shift` or `ctrl` and press down the left mouse button will give you the help.


## Tab Bar
This part main written for operating files opened in sublime but not gains input focus.

- The `Copy`, `Clone`, `Move`, `Rename`, `Delete`, `Copy File Path` commands are created for views have pointed to a file really exist in your computer.
- `New File in Folder` will create a file in the folder containing that file.
- `Open Containing Folder` will open the folder containing that file in you system's file manager.

[license-image]: https://img.shields.io/badge/license-MIT-blue.svg
