---
title: 'Gradle brainteasers 2/2: relocatable input files'
excerpt: 'There is no such thing as a "File" input...'
publishDate: 2024-07-17T08:41:15.615Z
image: '~/assets/images/2024-07-17_gradle-brainteasers-22-relocatable-input-files/ab1225bf-d512-4938-bb11-c38413464a0c.webp'
---

This is a follow up to [this other post](https://blog.mbonnin.net/gradle-brainteasers-12-aggregating-artifacts) about having fun with the Gradle APIs.

In this post, I'm talking about how I spent a shameful amount of time understanding how Gradle handles input files.

# The problem

The Apollo Gradle Plugin is generating Kotlin code from GraphQL files.

If you have GraphQL files like this:

```plaintext
.
└── src
    └── main
        └── graphql
            └── com
                └── example
                    ├── GetUser.graphql
                    ├── GetProduct.graphql
                    └── GetReview.graphql
```

The Apollo Compiler generates Kotlin classes like this:

```plaintext
com.example.GetUser
com.example.GetProduct
com.example.GetReview
```

<div data-node-type="callout">
<div data-node-type="callout-emoji">ℹ</div>
<div data-node-type="callout-text"><em>This behaviour of using the path as package name is </em><a target="_blank" rel="noopener noreferrer nofollow" href="https://apollographql.github.io/apollo-kotlin/kdoc/apollo-gradle-plugin-external/com.apollographql.apollo.gradle.api/-service/package-names-from-file-paths.html" style="pointer-events: none"><em>optional</em></a><em> and probably questionable but provides a very good use case for us diving into file inputs APIs.</em></div>
</div>

In a nutshell, the compiler looks at the relative path of the file and uses that as the package name.

# Build cache relocation

A naive implementation could use the "base" directory as input so that it can compute the package names:

```kotlin
  @get:PathSensitive(PathSensitivity.RELATIVE)
  @get:InputFiles
  abstract val inputFiles: Set<File>

  // The base directory to compute the package name
  // This isn't great
  @get:Input
  abstract var baseDir: String

  @TaskAction
  fun taskAction() {
    inputFiles.forEach {
      val packageName = it.relativeTo(File(baseDir))
                          .canonicalPath
                          .replace(File.separatorChar, '.')
      // ...
    }
  }
```

That works but it also completely breaks [build cache relocation](https://docs.gradle.org/current/userguide/build_cache_concepts.html#relocatability). If we were to copy our repository to another directory on our machine (or in CI), then no cache results could ever be reused.

# Entering FileCollection

The solution is to use [`FileCollection`](https://docs.gradle.org/current/javadoc/org/gradle/api/file/FileCollection.html) and its mutable cousin [`ConfigurableFileCollection`](https://docs.gradle.org/current/javadoc/org/gradle/api/file/ConfigurableFileCollection.html).

`FileCollection` is a [lazy API](https://docs.gradle.org/current/userguide/lazy_configuration.html) that can resolve [`Configuration`](https://mbonnin.medium.com/actual-footage-of-different-kinds-of-gradle-configurations-9678bd681793)s but most importantly may contain "roots". In other words, a `FileCollection` contains \`File\`s but also their relative path to the root(s).

<div data-node-type="callout">
<div data-node-type="callout-emoji">💡</div>
<div data-node-type="callout-text">Using<a target="_blank" rel="noopener noreferrer nofollow" href="https://docs.gradle.org/current/javadoc/org/gradle/api/tasks/PathSensitivity.html#RELATIVE" style="pointer-events: none"><code>PathSensitivity.RELATIVE</code></a> on a <code>java.io.File</code> property is the same as using <a target="_blank" rel="noopener noreferrer nofollow" href="https://docs.gradle.org/current/javadoc/org/gradle/api/tasks/PathSensitivity.html#NAME_ONLY" style="pointer-events: none"><code>PathSensitivity.NAME_ONLY</code></a> since it doesn't not contain any root.</div>
</div>

At a high level, **Gradle doesn't have**`java.io.File`**inputs**. It's always `java.io.File` + `"fileIdentifier"`.

`fileIdentifier` being a name, a relative or absolute path, or even empty if only the contents of the file matter and you're using [`PathSensitivity.NONE`](https://docs.gradle.org/current/javadoc/org/gradle/api/tasks/PathSensitivity.html#NONE).

So how do we get that identifier? Well, for `NAME_ONLY` we can use `file.name`, for `NONE`, we can use `""` and for `ABSOLUTE`, we can use `file.asbolutePath`. But what about `RELATIVE`?

The secret to getting the relative path from a `FileCollection` is using [`asFileTree`](<https://docs.gradle.org/current/javadoc/org/gradle/api/file/FileCollection.html#getAsFileTree()>) which returns the underlying `FileTree` if any (which is really a `FileForest` because `FileTree`s can contain multiple roots):

```kotlin
  @get:PathSensitive(PathSensitivity.RELATIVE)
  @get:InputFiles
  abstract val inputFiles: ConfigurableFileCollection

  @TaskAction
  fun taskAction() {
    inputFiles.asFileTree.visit {
      // Yay, we have the File here alongside its relative path 🎉
      val packageName = path.replace(File.separatorChar, '.')
      // do codegen
    }
  }
```

Using `ConfigurableFileCollection`, we get all the information about our files, including their relative path.

It's a very convenient API that non only allows resolving dependencies (`Configurations` are `FileCollections`) and filtering (`FileTree.include()`) and do so in a [lazy](https://docs.gradle.org/current/userguide/lazy_configuration.html) way but most importantly, they make it possible to model input files without breaking cache relocation! SUCCESS!

!\[\](https://cdn.hashnode.com/res/hashnode/image/upload/v1721037893936/f23ea5e9-1bd2-4b6e-8d08-13312133e60b.webp align="center")

Looking ahead, [Gratatouille](https://github.com/GradleUp/gratatouille) will not allow simple \`File\` inputs to model the fact that task inputs also have a name (even if empty). Hopefully that will make the task of writing Gradle tasks easier!

---

_Brainteasers pictures from _[_mtairymd_](https://www.instructables.com/member/mtairymd/)_ on _[_Instructables_](https://www.instructables.com/Metal-Wire-Puzzle-Solutions/)
