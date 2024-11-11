---
title: 'Actual footage of different kinds of Gradle Configurations'
excerpt: '"Configuration" is a terrible name...'
publishDate: 2021-05-31T00:00:00Z
image: '~/assets/images/2021-05-31_Actual-footage-of-different-kinds-of-Gradle-Configurations/1*E-uprnrV7_n-Y-I4s12aNQ.jpeg'
---

*The first time I heard about Gradle configurations, I thought it'd be about writing* *build.gradle**files and configuring some* *DSL**and writing* *{}**blocks. Then I started writing* [*plugins*](https://github.com/apollographql/apollo-android/tree/main/apollo-gradle-plugin)*and realized that they have a* [*configuration phase*](https://docs.gradle.org/current/userguide/build_lifecycle.html#sec:build_phases)*too that is run before execution.*

*Well these are all configurations for sure... They also hide another type of configuration, which plays a center role in Gradle dependency management: the* [*Configuration API*](https://docs.gradle.org/current/dsl/org.gradle.api.artifacts.Configuration.html)*.*

Everytime you add a new dependency to a project, you're actually using configurations behind the scenes:

```kotlin
dependencies {
  // This is using the "implementation" configuration    
  implementation("com.squareup.okhttp3:okhttp:4.9.0")
}
```

The [Gradle dependency management documentation](https://docs.gradle.org/current/userguide/core_dependency_management.html) is very detailed. It has a very detailed page about [terminology](https://docs.gradle.org/current/userguide/dependency_management_terminology.html) and another one on [resolvable vs consumable Configurations](https://docs.gradle.org/current/userguide/declaring_dependencies.html#sec:resolvable-consumable-configs) that I recommend reading. It's also a lot of information to process.

This article goes the other way and starts from the concrete example above to go up and expose the three different kinds of configurations in real life.

### A concrete example

To understand what `implementation()` does, let's start from scratch! Create a new empty Gradle project with a single `build.gradle.kts` file containing:

```kotlin
// build.gradle.kts
repositories {
    mavenCentral()
}
dependencies {
    implementation("com.squareup.okhttp3:okhttp:4.9.0")
}
```

Running `./gradlew dependencies` should fail:

```
$ ./gradlew dependencies
> Configure project :
e: build.gradle.kts:5:5: Unresolved reference: implementation
```

That's because `implementation` is not a regular method from the Gradle Core API, it is a [generated accessor](https://docs.gradle.org/current/userguide/kotlin_dsl.html#type-safe-accessors), generated automatically by Gradle to make it easier to work with the DSL (Groovy has the same syntax although it's more dynamic and doesn't rely on generated accessors). You don't have to rely on the generated accessors though. Everything is Gradle is doable using the plain Gradle APIs:

```kotlin
// That's the same thing without generated accessors
dependencies.add("implementation", "com.squareup.okhttp3:okhttp:4.9.0")
```

Running `./gradlew dependencies` should still fail:

```
$ ./gradlew dependencies
FAILURE: Build failed with an exception.
* Where:
Build file '~/git/configurations-ins-and-outs/build.gradle.kts' line: 5
* What went wrong:
Configuration with name 'implementation' not found.
```

Fair enough. Since we started from an empty `build.gradle.kts` file, Gradle doesn't even know what we're trying to do. `OkHttp` and `implementation` are JVM concepts so it makes sense that Gradle doesn't force it by default. In fact, the Java plugin creates the `implementation` configuration (see [doc](https://docs.gradle.org/current/userguide/java_plugin.html#sec:java_plugin_and_dependency_management)). Let's add it:

```kotlin
plugins {
    // java is a core plugin, no need to add a version, it will use the version of Gradle
    id("java")
}

repositories {
    mavenCentral()
}

dependencies.add("implementation", "com.squareup.okhttp3:okhttp:4.9.0")
```

Running `./gradlew dependencies` will now show a lot more information. The result is too long to be displayed here, but you should see something like this (test configurations omitted for clarity):

* `annotationProcessor` Annotation processors and their dependencies for source set 'main'.
* `apiElements` - API elements for main. (n)
* `archives` - Configuration for archive artifacts. (n)
* `compileClasspath` - Compile classpath for source set 'main'.
* `compileOnly` - Compile only dependencies for source set 'main'. (n)
* `default` - Configuration for default artifacts. (n)
* `implementation` - Implementation only dependencies for source set 'main'. (n)
* `runtimeClasspath` - Runtime classpath of source set 'main'.
* `runtimeElements` - Elements of runtime for main. (n)
* `runtimeOnly` - Runtime only dependencies for source set 'main'. (n)

Pheewww, that's a lot! We won't be able to cover all of them in this article but we'll cover the most representative ones. Let's skip the `default` configuration that is [now deprecated](https://docs.gradle.org/current/userguide/userguide_single.html#using_default_and_archives_configurations) and put aside the `archives` and `annotationProcessor` ones for now, that leaves us with `apiElements`, `compileClasspath`, `compileOnly`, `implementation`, `runtimeClasspath`, `runtimeElements` and `runtimeOnly`.

Let's start with the ubiquitous one, `implementation`.

### "Bucket of dependencies" Configurations

`implementation` is a "bucket of dependencies" Configuration. This is where you add dependencies like `com.squareup.okhttp3:okhttp:4.9.0`. To get the list of dependencies (but not their files, more on that later), you can do things like:

```kotlin
configurations["implementation"].dependencies.forEach {
    println("dependency: $it")
}
```

Run `./gradlew` to trigger the compilation and evaluation of your `build.gradle.kts` script:

```
$ ./gradlew
> Configure project :
dependency: DefaultExternalModuleDependency{group='com.squareup.okhttp3', name='okhttp', version='4.9.0', configuration='default'}
```

So far so good! The dependency you just added has been registered. It's registered as a `DefaultExternalModuleDependency` because it gets its file from an external repo (MavenCentral here), that's fair. Ultimately though, you want to get access to the `okhttp` jar as well as its transitive dependencies: `okio` and `kotlin-stdlib`. The way this is usually done is by reading files directly from the `Configuration`. Indeed, a [Configuration](https://docs.gradle.org/current/javadoc/org/gradle/api/artifacts/Configuration.html) extends from a [FileCollection](https://docs.gradle.org/current/javadoc/org/gradle/api/file/FileCollection.html) so it has a [getFiles()](https://docs.gradle.org/current/javadoc/org/gradle/api/file/FileCollection.html#getFiles--)[method](https://docs.gradle.org/current/javadoc/org/gradle/api/file/FileCollection.html#getFiles--). Let's try to display the files in our configuration, this is called resolving the configuration:

```kotlin
configurations["implementation"].files.forEach {
    println("file: $it")
}
```

That shouldn't go too well:

```
$ ./gradlew 

[...]

* What went wrong:
Resolving dependency configuration 'implementation' is not allowed as it is defined as 'canBeResolved=false'.
Instead, a resolvable ('canBeResolved=true') dependency configuration that extends 'implementation' should be resolved.
```

💥 Damn, this is where things get fun... Indeed, if you remember the results of the first `./gradlew dependencies`, there was this line:

```
* `implementation` - Implementation only dependencies for source set 'main'. (n)
[...]
(n) - Not resolved (configuration is not meant to be resolved)
```

Getting the list of jar files contained in the `implementation` configuration, i.e. resolving it, is not possible. If you dump `configurations["implementation"].isCanBeResolved`, you will see it will indeed be `false`. This configuration holds dependencies declarations but cannot be resolved itself. For this, you'll need resolvable configurations (see [doc](https://docs.gradle.org/current/userguide/declaring_dependencies.html#sec:resolvable-consumable-configs)).

### Resolvable Configurations

If you look at the earlier `./gradlew dependencies` output, you can find two resolvable configurations.


Both these configurations **don't** have a `(n)` in front of them, meaning you **can** resolve them, Let's do this:

```
configurations["compileClasspath"].files.forEach {
    println("compileJar: $it")
}
```

Output: 

```
$ ./gradlew 

> Configure project :
dependency: DefaultExternalModuleDependency{group='com.squareup.okhttp3', name='okhttp', version='4.9.0', configuration='default'}
compileJar: ~/.gradle/caches/modules-2/files-2.1/com.squareup.okhttp3/okhttp/4.9.0/8e17601d3bdc8cf57902c154de021931d2c27c1/okhttp-4.9.0.jar
compileJar: ~/.gradle/caches/modules-2/files-2.1/com.squareup.okio/okio/2.8.0/49b64e09d81c0cc84b267edd0c2fd7df5a64c78c/okio-jvm-2.8.0.jar
compileJar: ~/.gradle/caches/modules-2/files-2.1/org.jetbrains.kotlin/kotlin-stdlib/1.4.10/ea29e063d2bbe695be13e9d044dcfb0c7add398e/kotlin-stdlib-1.4.10.jar
compileJar: ~/.gradle/caches/modules-2/files-2.1/org.jetbrains.kotlin/kotlin-stdlib-common/1.4.10/6229be3465805c99db1142ad75e6c6ddeac0b04c/kotlin-stdlib-common-1.4.10.jar
compileJar: ~/.gradle/caches/modules-2/files-2.1/org.jetbrains/annotations/13.0/919f0dfe192fb4e063e7dacadee7f8bb9a2672a9/annotations-13.0.jar
```

Huge success! You just resolved your first configuration. In fact this is the same thing that the Java/Kotlin compiler will use to determine what jars to put on the compile classpath (hence the `"compileClasspath"` name!). Whenever you need to compile against `okhttp`, the compiler also needs `okio` and `kotlin-stdlib`. It needs `okio` because `okio` is in the `okhttp` API. Function such as [ResponseBody.source()](https://square.github.io/okhttp/4.x/okhttp/okhttp3/-response-body/source/) expose a [okio.BufferedSource](https://square.github.io/okio/2.x/okio/okio/-buffered-source/index.html) so the compiler needs that symbol in the compile classpath (you can read more about api vs implementation [here](https://jeroenmols.com/blog/2017/06/14/androidstudio3/)).

What about `runtimeClasspath` then? Well in this specific case, it's going to be the same. This is because the exact same dependencies are needed both to compile the project and to run it. This isn't a general rule though. If `okhttp` wrapped all the `okio` types and did not expose them, `okio` wouldn't be needed to compile the project.

In addition to the above resolvable configurations, the `java` plugin creates 2 non-resolvable, implementation-like, "bucket of dependencies", configurations:

* `compileOnly` to add a dependency to `compileClasspath` only. This is typically what's used by Gradle plugins to compile against the Gradle API but not use it at runtime since it's provided by the Gradle instance that runs the plugin.
* `runtimeOnly` to add a dependency to `runtimeClasspath` only. This is used less often but is useful in cases where multiple implementations of the same API could be made available at runtime. For an example using [ServiceLoader](https://docs.oracle.com/javase/7/docs/api/java/util/ServiceLoader.html) or another mechanism. This happens with logging frameworks like [SLF4J](http://www.slf4j.org/). The project is compiled using an abstract logger. The actual implementation is being loaded at runtime but not needed during compilation.

Using [Configuration.extendsFrom()](https://docs.gradle.org/current/dsl/org.gradle.api.artifacts.Configuration.html#org.gradle.api.artifacts.Configuration:extendsFrom), Gradle can make dependencies from these configurations available to the resolvable configurations. When compileClasspath extends from compileOnly, all the files from compileOnly will be available in compileClasspath.

In practice, the `java` plugin uses the following (from the [doc](https://docs.gradle.org/current/userguide/java_plugin.html#tab:configurations)):

* implementation (non resolvable)
* compileOnly (non resolvable)
* runtimeOnly (non resolvable)
* compileClasspath extends compileOnly, implementation
* runtimeClasspath extends runtimeOnly, implementation

The first three are where you add dependencies. The last two are used by the JavaCompile task and runners.

Note that there is no `api` configuration in the list. This is because `api` only make sense for library projects that can be consumed by another project. The `api` configuration is added by the [java-library](https://docs.gradle.org/current/userguide/java_library_plugin.html#sec:java_library_separation)[plugin](https://docs.gradle.org/current/userguide/java_library_plugin.html#sec:java_library_separation) (and not the `java` one)

If you go back to the original list of configurations, we have covered `compileClasspath`, `compileOnly`, `implementation`, `runtimeClasspath` and `runtimeOnly`.

So what are `runtimeElements` and `apiElements`?

### Consumable Configurations

`runtimeElements` and `apiElements` are [consumable](https://docs.gradle.org/current/userguide/declaring_dependencies.html#sec:resolvable-consumable-configs)[configurations](https://docs.gradle.org/current/userguide/declaring_dependencies.html#sec:resolvable-consumable-configs). Consumable configurations are meant to be used by other projects consuming this project. I know this is very close to "resolvable". In Gradle terminology:

* Resolvable is to read the files from a configuration **inside** a project
* Consumable is to expose files to consumers **outside** the project

It makes more sense for library projects. For some reason, it's also added for non-library projects. I'm guessing some project could consume the executable jar too. In all cases, you can get the consumable configurations with `./gradlew outgoingVariants`:

```
$ ./gradlew outgoingVariants
> Task :outgoingVariants
--------------------------------------------------
Variant apiElements
--------------------------------------------------
Description = API elements for main.

Capabilities
    - :gradle-configurations:unspecified (default capability)
Attributes
    - org.gradle.category            = library
    - org.gradle.dependency.bundling = external
    - org.gradle.jvm.version         = 11
    - org.gradle.libraryelements     = jar
    - org.gradle.usage               = java-api

Artifacts
    - build/libs/gradle-configurations.jar (artifactType = jar)

--------------------------------------------------
Variant runtimeElements
--------------------------------------------------
Description = Elements of runtime for main.

Capabilities
    - :gradle-configurations:unspecified (default capability)
Attributes
    - org.gradle.category            = library
    - org.gradle.dependency.bundling = external
    - org.gradle.jvm.version         = 11
    - org.gradle.libraryelements     = jar
    - org.gradle.usage               = java-runtime

Artifacts
    - build/libs/gradle-configurations.jar (artifactType = jar)
```

The consumable configurations are used during [variant-aware selection](https://docs.gradle.org/current/userguide/variant_model.html#understanding-variant-selection). If you have seen a message such as below, chances are that some consumable configuration exposes incompatible attributes:

```
> Could not resolve all files for configuration ':app:configuration'.
   > The consumer was configured to find attribute 'com.android.build.api.attributes.BuildTypeAttr' with value 'release'. However we cannot choose between the following variants of project :lib:
```

A consumable configuration can have attributes using the [Configuration.attributes](https://docs.gradle.org/current/javadoc/org/gradle/api/attributes/HasConfigurableAttributes.html#attributes-org.gradle.api.Action-)[API](https://docs.gradle.org/current/javadoc/org/gradle/api/attributes/HasConfigurableAttributes.html#attributes-org.gradle.api.Action-) and then [expose artifacts](https://docs.gradle.org/current/userguide/cross_project_publications.html#sec:simple-sharing-artifacts-between-projects) using the [Project.artifacts](https://docs.gradle.org/current/javadoc/org/gradle/api/Project.html#artifacts-groovy.lang.Closure-)[API](https://docs.gradle.org/current/javadoc/org/gradle/api/Project.html#artifacts-groovy.lang.Closure-). There's a lot in there and that'll certainly deserve a separate article.

### Conclusion

The Configuration API is a corner stone of the dependency management in Gradle. Despite all of them being Configurations, the "bucket of dependencies", resolvable and consumable configuration are very different. I hope this simple example helps to understand what are the different types of Configurations. If you ever want to double check, you can always dump the values of `isCanBeResolved` and `isCanBeConsumed`:

```kotlin
configurations.all {
    println(String.format("%-26s resolvable=%-5s consumable=%-5s", name, isCanBeResolved, isCanBeConsumed))
}
```

Output:

```
implementation             resolvable=false consumable=false
runtimeOnly                resolvable=false consumable=false
compileOnly                resolvable=true  consumable=true 

runtimeClasspath           resolvable=true  consumable=false
compileClasspath           resolvable=true  consumable=false

apiElements                resolvable=false consumable=true 
runtimeElements            resolvable=false consumable=true 
```

In this article, we've seen the three different types of configurations:

* **Bucket of dependencies** ( `implementation`, `runtimeOnly`, `compileOnly`) are used by the user to declare dependencies. They are neither resolvable nor consumable... ...well, except for `compileOnly` that is both! I didn't expected that when I started writing this article. If anyone has an explanation, I'll take it\*.
* **Resolvable configurations** ( `runtimeClasspath` and `compileClasspath`) are the resolvable configurations to be used inside the project by tasks like compileJava and compileKotlin to get the actual jar files.
* **Consumable configurations** ( `apiElements` and `runtimeElements`): are the consumable configurations to be consumed by other projects and used by variant aware selection. You can see them with `./gradlew outgoingVariant`.

When in doubt, always refer to the [official terminology doc](https://docs.gradle.org/current/userguide/dependency_management_terminology.html#sub:terminology_component) which is super useful!

Happy configuring!

\*: I got an explanation from [Cedric Champeau](https://melix.github.io/blog/)! `compileOnly` was present before `runtimeOnly` and has both flags set to true for backward compatibility reasons. And actually, both flags are set to false by default starting with Gradle 7.

By [Martin Bonnin](https://medium.com/@mbonnin) on [May 31, 2021](https://medium.com/p/9678bd681793).

Photo: [Elephant](https://flic.kr/p/iKcVx8) by [flowcomm](https://www.flickr.com/photos/flowcomm/)

[Canonical link](https://medium.com/@mbonnin/actual-footage-of-different-kinds-of-gradle-configurations-9678bd681793)

Exported from [Medium](https://medium.com) on November 9, 2024.
