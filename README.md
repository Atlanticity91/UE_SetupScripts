UE Solution Scripts
---

> [!WARNING]
> The internal python script is only made and tested on Widnows for the moment.

A common batch + python script to speed up solution cleaning and regeneration for unreal engine 5 projects.

# Install
1. Simply add the Scripts folder + Build-Windows.bat to the root of your unreal engine 5 project.
2. Replace `GameName` inside the `Build-Windows.bat` by the name of yout .uproject solution.
3. Replace the `UE_5.6` by your target engine folder version name.
4. Internaly the python script use `EPIC_DIR` custom environement variable, it should be set to epic game installation folder or root folder where you install unreal engine like `F:\Epic Games\` for me.

# Use
Any time your need to rebuild the solution ( when this tool is created some time to update plugins code you need full solution cleaning + rebuild ) simply launch `Build-Windows.bat` and wait for completion before launching the visual studio fresh solution.
