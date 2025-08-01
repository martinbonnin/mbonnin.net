---
title: '`@InputDirectory` is a lie'
excerpt: "It's always files!"
publishDate: 2025-01-27T00:00:00Z
image: '~/assets/images/2025-01-22_input_directory_is_a_lie/thumbnail.jpg'
---

Do you have a compiler that takes source files and compile them?

In those cases, it's tempting to use [`@InputDirectory`](https://docs.gradle.org/current/javadoc/org/gradle/api/tasks/InputDirectory.html). A single annotation, just feed the whole directory to your task. Simple.

Or is it?

After years of fighting against the system, I have just realized that `@InputDirectory` is pretty much a footgun.

In best cases, it lacks flexibility. In worst cases, it's a source of bugs. In most cases, you should use [`@InputFiles`](https://docs.gradle.org/current/javadoc/org/gradle/api/file/ConfigurableFileCollection.html) and a [`ConfigurableFileCollection`](https://docs.gradle.org/current/javadoc/org/gradle/api/file/ConfigurableFileCollection.html) instead.

Why? Let's dive in!

## It's all files

Gradle is great because it deals with [incremental builds](https://docs.gradle.org/current/userguide/more_about_tasks.html#sec:incremental_tasks) automatically. If nothing changes, no work is done, saving you a bunch of time while iterating on that single feature.

Unlike older build systems like [GNU Make](https://www.gnu.org/software/make/manual/make.html), which store and compare timestamps, Gradle stores and compares the (hashed) contents of the inputs. If your inputs do not change, your task doesn't run, regardless of the file timestamps (also allows cool features like a [remote build cache](https://docs.gradle.org/current/userguide/build_cache.html)).

If your input is a file, Gradle reads all its contents and hashes it. If your input is a directory, Gradle reads each file recursively and hashes the contents.

But unlike a flat file, a directory also has a structure. That structure may be important to your compile task. Typically, the name of the directories are important.

This is where Gradle [`@PathSensitive`](https://docs.gradle.org/current/javadoc/org/gradle/api/tasks/PathSensitive.html) comes into play:

```java
/**
 * Annotates a task file property, specifying which part of the file
 * paths should be considered during up-to-date checks.
 *
 * <p>If a {@link org.gradle.api.Task} declares a file property without
 * this annotation, the default is {@link PathSensitivity#ABSOLUTE}.</p>
 *
 */
@Target({ElementType.METHOD, ElementType.FIELD})
public @interface PathSensitive {
    PathSensitivity value();
}
```

`@PathSensitive` tells Gradle how to hash the path of each file. It can take different values:

- `NONE`: Ignore file paths and directories altogether.
- `NAME_ONLY`: Consider only the name of files and directories.
- `RELATIVE`: Use the location of the file related to a hierarchy.
- `ABSOLUTE`: Consider the full path of files and directories.

Note how the `ABSOLUTE` default completely prevents any kind of remote build cache. You should definitely switch your default to `RELATIVE`.

Note also how `RELATIVE` is vague about what the root of the hierarchy is and how, in the case of a directory, the path sensitivity applies both to the path of the directory itself and also to the paths of its contents. Navigating the Gradle internals is left as an exercise to the reader.

## `@InputDirectory` is all or nothing

Whenever you use `@InputDirectory`, you're passing a full recursive directory and relative paths.

If you have a `com/example` hierarchy in your `build/generated/root` directory, you may think you're passing this:

```
build/generated/root
```

But in fact, what you're really passing is a list of `(file contents, relative path)`:

```
contents1, "com/example/file1"
contents2, "com/example/file2"
contents3, "com/example/file3"
...
```

This has several problems:

- Your compiler may want to compile files from different directories.
- Your compiler may want to compile a subset of the files in a given directory (for an example, only the files with a given extension).
- Your compiler and Gradle need to agree on how to compute the relative path. If not, weird caching issues will happen.

To make things worse, this is all implicit. It took me way too much time to understand what was going on under the hood and I wasted many hours trying to reimplement Gradle normalization for no good reason.

## Entering `ConfigurableFileCollection`

As we've seen most tasks work with file inputs, not directories.

[`ConfigurableFileCollection`](https://docs.gradle.org/current/javadoc/org/gradle/api/file/ConfigurableFileCollection.html) is the main class to represent a lazy collection of `File` (as it turns out, it may contain both regular files and directories, more on that later).

You can use `ConfigurableFileCollection` in your tasks like so:

```kotlin
  @get:InputFiles
  @get:PathSensitive(PathSensitivity.RELATIVE)
  abstract val sourceFiles: ConfigurableFileCollection
```

`ConfigurableFileCollection` allows for a lot more flexibility:

```kotlin
// Adding a single file
sourceFiles.from("inputFile1.foo")
// Adding a directory recursively
sourceFiles.from(fileTree("inputDir1"))
// Adding a second directory recursively
sourceFiles.from(fileTree("inputDir2"))
// Only add the `.foo` files in `inputDir3`
sourceFiles.from(fileTree().apply {
  from("inputDir3")
  include("**/*.foo")
})
// Add the output of a taskProvider, carrying task dependency lazily
sourceFiles.from(taskProvider)
```

You're not limited to a single directory anymore. The user of your task has full control over what is being wired.

It is now explicit that your task works with files.

To consume the files, use `asFileTree`:

```kotlin
sourceFiles.asFileTree.visit {
  if (file.isFile) {
    // You can use the file contents here
    file.readText()
    // And access the normalized file path (used for caching) too!
    println(path)
  }
}
```

_Note: as you can see above, `ConfigurableFileCollection` may still contain directories, for an example if created from `fileTree()`. The meaning of a directory of up-to-date checks isn't 100% clear to me. Do you need to know if there is an empty directory? I usually don't and just filter the directories out._

No more having to walk a directory, assuming you would do it just like Gradle would do it. It's all files. Always has been.

For this reason, [Gratatouille forbids input directories](https://github.com/GradleUp/gratatouille/blob/main/gratatouille-runtime/src/main/kotlin/gratatouille/api.kt#L132) and only has files.

## What about `@OutputDirectory`?

If you've read so far, you might think everything is a file, and therefore we might as well model the task outputs as `FileCollection` symmetrically. But that would be too easy. Inputs and outputs are fundamentally asymmetrical.

Inputs are owned by the caller and need to provide flexibility to accommodate for different cases and may overlap.

Outputs are owned by the task and need to provide predictability and structure. They must not overlap.

Furthermore, using `@OutputDirectory` for outputs may allow to display generated directories using a separate icon in the IDE. For UI purposes, making the difference between a file and a directory is useful!

## Conclusion

If all the files in your directory as well as their relative path to your directory are relevant to your task, then `@InputDirectory` saves you a few lines of code.

On the other hand, if your task only considers the name of your files and/or take files from several directories, `@InputFiles` allows to model with a lot more granularity. And the above case can also be modeled with `@InputFiles`.

All in all, `@InputFiles` is a lot more flexible and explicit than `@InputDirectory`. I'll use that moving forward and you should too!
