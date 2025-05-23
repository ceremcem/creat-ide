# Creat-IDE

## Example POC

```
python3 workspace-manager.py
```

TODO: 
 1. Launch the selected app
 2. Adjust its window size and position accordingly
 3. Make the apps follow the creat-ide resize
 4. Save the configurations to the workspace


## Status 

This project is waiting for the application of: https://github.com/ceremcem/creat-ide/issues/1

> Former approach: [this](https://stackoverflow.com/questions/29948105/how-to-embed-an-application-into-another-application-dynamically) combined by [that](https://superuser.com/questions/1360453/how-to-use-more-than-one-window-manager-concurrently)


## Description 

Every project needs a different type of IDE. If you create a electronic circuit board, that will need a serial port terminal, you will open 

- a code editor, 
- a remote debugger window, 
- a serial port terminal, 
- an electronic design automation software, 
- etc... 

On the other hand, If you need a web application development, 

- you will put your favourite web browser on one side, 
- it's debugger window and 
- your code editor on the other side. 

You will possibly need another layout for updating your server, possibly with SSH connection.

## Problem

There is no IDE that puts all these together. You will have to use different applications for each purpose, open them simultaneously and precisely adjust the placement of these windows side by side. You have to 

- open every single application (there is [service-runner](https://github.com/aktos-io/service-runner) for that purpose though)
- adjust window sizes accordingly

whenever you start your project and close every single application when you stop your development. 

If you want to resize a window, you will have to resize the neighbours.

## Solution 

So we need actually an application that will hold these windows and hopefully create some workspaces: 

![image](https://user-images.githubusercontent.com/6639874/34055183-20574e76-e1df-11e7-9e29-3cf3ff5a7a51.png)

These panes will be controlled like Blender:

![detachwindows](https://user-images.githubusercontent.com/6639874/34056304-8594d002-e1e3-11e7-95b8-c5f3b4c6a25e.gif)


