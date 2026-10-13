/**
 * Windows x64 GUI entry point for the private CPython distribution.
 *
 * Resolve every runtime path relative to this executable, load Python from the
 * adjacent runtime directory, and preserve Unicode command-line arguments.
 * No shell, system Python, installer, registry edit, or elevation is used.
 */
#define WIN32_LEAN_AND_MEAN
#ifndef UNICODE
#define UNICODE 1
#endif
#ifndef _UNICODE
#define _UNICODE 1
#endif
#include <windows.h>
#include <shellapi.h>
#include <wchar.h>
#include <stdlib.h>
#include <stdio.h>

#define PATH_CAPACITY 32768
typedef int (__cdecl *PythonMain)(int, wchar_t **);

/** Display an actionable startup error without opening a console window. */
static int startup_error(const wchar_t *detail) {
    wchar_t message[2048];
    swprintf(message, 2048,
        L"QIIME 2 Provenance Studio could not start.\n\n%ls\n\n"
        L"Extract the entire ZIP to a local folder, then run the EXE there.\n"
        L"Keep the runtime and app folders beside the EXE.\n\nWindows error: %lu",
        detail, GetLastError());
    MessageBoxW(NULL, message, L"QIIME 2 Provenance Studio", MB_OK | MB_ICONERROR);
    return 1;
}

/** Enter the app in this native process, with Python's isolated mode enabled. */
int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR command, int show) {
    (void)instance;
    (void)previous;
    (void)command;
    (void)show;
    wchar_t *root = calloc(PATH_CAPACITY, sizeof(wchar_t));
    wchar_t *library_path = calloc(PATH_CAPACITY, sizeof(wchar_t));
    wchar_t *script_path = calloc(PATH_CAPACITY, sizeof(wchar_t));
    if (!root || !library_path || !script_path) {
        free(root); free(library_path); free(script_path);
        return startup_error(L"Insufficient memory.");
    }
    DWORD length = GetModuleFileNameW(NULL, root, PATH_CAPACITY);
    wchar_t *separator = wcsrchr(root, L'\\');
    if (!length || length >= PATH_CAPACITY || !separator) {
        free(root); free(library_path); free(script_path);
        return startup_error(L"Cannot locate the application folder.");
    }
    *separator = L'\0';
    if (swprintf(library_path, PATH_CAPACITY, L"%ls\\runtime\\python313.dll", root) < 0 ||
        swprintf(script_path, PATH_CAPACITY, L"%ls\\app\\bootstrap.py", root) < 0) {
        free(root); free(library_path); free(script_path);
        return startup_error(L"The application path is too long.");
    }

    /* Resolve native dependencies from the selected runtime and Windows only. */
    SetDefaultDllDirectories(LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
    HMODULE python = LoadLibraryExW(library_path, NULL,
        LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
    if (!python) {
        free(root); free(library_path); free(script_path);
        return startup_error(L"The bundled Python runtime is missing or cannot be loaded.");
    }
    PythonMain python_main = (PythonMain)(void *)GetProcAddress(python, "Py_Main");
    if (!python_main || GetFileAttributesW(script_path) == INVALID_FILE_ATTRIBUTES) {
        free(root); free(library_path); free(script_path);
        FreeLibrary(python);
        return startup_error(L"Required application files are missing.");
    }
    int original_count = 0;
    wchar_t **original = CommandLineToArgvW(GetCommandLineW(), &original_count);
    wchar_t **arguments = calloc((size_t)original_count + 7, sizeof(wchar_t *));
    if (!original || !arguments) {
        LocalFree(original); free(arguments);
        free(root); free(library_path); free(script_path);
        FreeLibrary(python);
        return startup_error(L"Cannot read command-line arguments.");
    }
    arguments[0] = original[0];
    arguments[1] = L"-I";  /* Ignore system/user Python environments. */
    arguments[2] = L"-B";  /* Keep the portable application directory read-only. */
    arguments[3] = L"-X";
    arguments[4] = L"utf8";
    arguments[5] = script_path;
    for (int index = 1; index < original_count; ++index) {
        arguments[index + 5] = original[index];
    }
    int result = python_main(original_count + 5, arguments);
    LocalFree(original);
    free(arguments); free(root); free(library_path); free(script_path);
    FreeLibrary(python);
    return result;
}
