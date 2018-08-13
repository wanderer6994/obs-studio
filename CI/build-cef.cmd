appveyor DownloadFile "%CefUrl%" -FileName "%CefZip%"
7z x "%CefZip%"

cmake ^
	-G"%CmakeGenerator%" ^
	-A x64 ^
	-T "host=x64" ^
	-H"%CefPath%" ^
	-B"%CefBuildPath%" ^
	-DCEF_RUNTIME_LIBRARY_FLAG="/MD"

cmake ^
	--build "%CefBuildPath%" ^
	--config Release ^
	--target libcef_dll_wrapper ^
	-- /logger:"C:\Program Files\AppVeyor\BuildAgent\Appveyor.MSBuildLogger.dll"