package edu.ncsu.utils;

import org.apache.commons.lang3.StringUtils;

import java.io.File;
import java.io.FilenameFilter;
import java.util.ArrayList;
import java.util.List;

public class Utils {

    /**
     * Create a directory if it does not exist
     * @param dirName
     */
    public static void mkdir(String dirName) {
        File dir = new File(dirName);
        if (!dir.exists()) {
            dir.mkdirs();
        }
    }

    /***
     * List directories in folder
     * @param dirName Name of directory
     * @return List of subdirectories
     */
    public static String[] listDir(String dirName) {
        File dir = new File(dirName);
        String[] directories = dir.list(new FilenameFilter() {
            @Override
            public boolean accept(File dir, String name) {
                return new File(dir, name).isDirectory();
            }
        });
        return directories;
    }

    /**
     * Check if the file exists.
     * @param fileName Name of the file
     * @return True if file exists else False.
     */
    public static boolean fileExists(String fileName) {
        File file = new File(fileName);
        return file.exists();
    }

    /**
     * List all files in folder with the matching extension.
     * @param folderPath Path of the folder
     * @param extension Extension to match
     * @param isAbsolute If true, returns absolute path else relative path.
     * @param checkNest If true, checks nested directories as well
     * @return
     */
    public static List<String> listFilesWithExtension(String folderPath, final String extension,
                                                      boolean isAbsolute, boolean checkNest) {
        File directory = new File(folderPath);
        List<String> files = new ArrayList<>();
        for (File file : directory.listFiles()) {
            if (file.isFile() && file.getName().endsWith(extension)) {
                if (isAbsolute)
                    files.add(file.getAbsolutePath());
                else
                    files.add(file.getName());
            } else if (checkNest && file.isDirectory()) {
                files.addAll(listFilesWithExtension(file.getAbsolutePath(), extension, isAbsolute, true));
            }
        }
        return files;
    }

    /***
     * Join a list of path by the file separator
     * @param paths - Array of paths to join.
     * @return
     */
    public static String pathJoin(String... paths) {
        return StringUtils.join(paths, File.separator);
    }
}
