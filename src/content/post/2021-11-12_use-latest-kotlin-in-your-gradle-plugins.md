---
title: 'Use latest Kotlin in your Gradle plugins'
excerpt: 'A relocating tale about R8, classloaders and metadata......'
publishDate: 2021-11-12T15:13:39.328Z
image: '~/assets/images/2021-11-12_use-latest-kotlin-in-your-gradle-plugins/3rMt16zUJ.jpeg'
---

_This is the story of how I got down the rabbit hole of relocating classes while trying to workaround the Gradle classloaders and fixed Kotlin runtime limitations. I'm not sure if I'd recommend trying this at home but this was an interesting journey! Read this (long) post if you're curious about what it takes to use the latest version of Kotlin in your plugins._

_If you prefer reading source code, read the_ [_matching pull request in apollo-android_](https://github.com/apollographql/apollo-android/pull/3542/)

**Note**: This post was written when Kotlin 1.5 was released and Gradle 7.1 was using 1.4. The same is true with Kotlin 1.7 (or any other newer versions)

### The 🐔 and 🥚 problem

Say you have a Gradle build. This Gradle build uses Kotlin `build.gradle.kts` scripts that you wrote. These scripts themselves declare plugins:

```plaintext
// build.gradle.kts
plugins {
  id("org.jetbrains.kotlin.jvm").version("1.5.30")
  id("com.example").version("1.0")
}
```

Let's also assume that the `com.example` plugin uses `kotlin-stdlib:1.5` and uses some new 1.5 APIs like [`lowercase`](https://kotlinlang.org/docs/whatsnew15.html#stable-locale-agnostic-api-for-upper-lowercasing-text).

Gradle needs to compile these scripts using the 1.4 embedded Kotlin compiler, run them, resolve plugins and their dependencies and put them in the buildscript classpath. So the build environment will be like:

```plaintext
+--- org.jetbrains.kotlin:kotlin-gradle-plugin:1.5.30
|    +--- org.jetbrains.kotlin:kotlin-gradle-plugin-api:1.5.30
|    |    \--- org.jetbrains.kotlin:kotlin-stdlib:1.5.30 -> 1.5.31
|    |         +--- org.jetbrains:annotations:13.0
|    |         \--- org.jetbrains.kotlin:kotlin-stdlib-common:1.5.31
+--- com.example:plugin:1.0
|    +--- org.jetbrains.kotlin:kotlin-stdlib:1.5.31
```

Now in order to run the dependency resolution, and because the scripts themselves are written in Kotlin, Gradle needs a stdlib even before it starts the build \[^1\].

This is were the chicken and egg problem kicks in. It's too early for Gradle to know the build will ultimately require 1.5 so Gradle puts the version it knows about in the classpath. That's version 1.4 💥.

When our `com.example` plugin runs, it will crash because `lowercase` doesn't exist in 1.4 \[^2\]

Even if it doesn't crash, chances are that you will see a lot of these lines:

```plaintext
w: Runtime JAR files in the classpath should have the same version. These files were found in the classpath:
    /home/runner/.gradle/wrapper/dists/gradle-7.0-all/9m115ut5nwvtxli7nys8pggfr/gradle-7.0/lib/kotlin-stdlib-1.4.31.jar (version 1.4)
    /home/runner/.gradle/wrapper/dists/gradle-7.0-all/9m115ut5nwvtxli7nys8pggfr/gradle-7.0/lib/kotlin-stdlib-common-1.4.31.jar (version 1.4)
...
```

This problem is discussed at length in [Github issue #16345](https://github.com/gradle/gradle/issues/16345). There are multiple workarounds or fixes. Let's go over a few of them and see how relocation can help.

## Solution \#1: Don't use Kotlin 1.5 in plugins!

After all, it's not such a huge deal, right? We've lived without `lowercase` for years so we can wait a bit more. What's more, the Kotlin compiler supports `apiVersion`. If you're a plugin author, you can make sure your bytecode doesn't use any 1.5 APIs:

```plaintext
compileKotlin {
  kotlinOptions {
    // Compile against 1.4 stdlib for the time being to make sure it works
    // with a wide range of Gradle versions.
    apiVersion = "1.4"
  }
}
```

That works but not being able to use the latest APIs feels bad. What's even worse is that `apiVersion` only works for your code, not for dependencies of your plugin. If you want to use okio in your Gradle plugins, [you're out of luck](https://github.com/square/okio/pull/960) with this solution.

## Solution \#2: Use Gradle Worker's API

For plugins, Gradle exposes the [Worker API](https://docs.gradle.org/current/userguide/worker_api.html). Especially, it has a [classloaderIsolation](https://docs.gradle.org/current/userguide/worker_api.html#changing_the_isolation_mode) mode that allows to isolate the plugin's classloader from the Gradle classloader.

It's a bit more work because you'll have to pass parameters to the worker but it gives full flexibility about the classpath. I'm still not 100% clear how much this is a rock solid solution given that the public API (extensions, tasks, etc...) will also use Kotlin and this cannot be moved to a worker. Maybe if you make sure the public API is simple enough to not use any new API and keep the tasks implementations for 1.5... I'd be curious if anyone has had any success with this.

## Solution \#3: Always update Gradle to the latest version

Given that Gradle is relatively fast to update the embedded version of Kotlin, you can wait until it's updated before using it in your plugin. That's always too much waiting but it can be acceptable in most cases. Of course, that also means any user of your plugin is also on this fast update path, which might or might not be acceptable.

## Solution \#4: Relocation!

Finally, the solution that should work in all cases!

No need to wait or change your plugin code, just ship your own kotlin-stdlib as part of your plugin jar. As a nice bonus, that even fixes other issues with [buildSrc](https://github.com/gradle/gradle/issues/8301) or [classloaders](https://github.com/apollographql/apollo-android/issues/2939). Sounds simple, right? Well... let's see what it takes to relocate the `kotlin-stdlib`

### Relocating with Shadow?

The [Gradle Shadow Plugin](https://imperceptiblethoughts.com/shadow/) has been used to relocate countless Gradle plugins like [SQLDelight](https://www.alecstrong.com/posts/shading/). It's working well most of the time. Unfortunately, when it comes to Kotlin, there are some details that make it harder to use. The biggest issue is that Shadow uses [MavenShade](https://maven.apache.org/plugins/maven-shade-plugin/) under the hood and this [relocates constant strings that shouldn't be](https://github.com/johnrengelman/shadow/issues/232). In practice, using it to relocate `kotlin` will transform code like this:

```kotlin
// Get the Kotlin plugin extension (to get sourceSets or anything else)
project.extensions.getByName("kotlin")
```

into code like that:

```kotlin
// Yikes, there's no "com.your.plugin.relocated.kotlin" extension :-(
project.extensions.getByName("com.your.plugin.relocated.kotlin")
```

This is pretty unexpected and breaks most of plugins interacting with the Kotlin plugin.

For plugins that generate source code and contain a lot of package names, this might require even weirder [workarounds](https://github.com/apollographql/apollo-android/blob/f72c3afd17655591aca90a6a118dbb7be9c50920/apollo-compiler/src/main/kotlin/com/apollographql/apollo/compiler/codegen/kotlin/OkioJavaTypeName.kt#L19).

### Using R8

[R8](https://r8.googlesource.com/r8) is Google's replacement for Proguard. While R8 is mainly used for Android, it can be used with any jar file too, [including Kotlin](https://jakewharton.com/shrinking-a-kotlin-binary/). By using [proguard rules](https://www.guardsquare.com/manual/configuration/usage), we get a lot more control about the relocation, what is kept and what is not.

Unfortunately, R8 is not super easy to consume. It is only published in minified form at maven.google.com. I wrote [a small Kotlin script](https://github.com/martinbonnin/kscripts/blob/master/r8_release.main.kts) to publish the non-minimized artifacts to [Maven Central](https://repo1.maven.org/maven2/net/mbonnin/r8/r8/). I also wrote a small plugin to make it easier to use R8 with Gradle. It's named GR8 because it's great and you can find it on Github at https://github.com/GradleUp/gr8.  
(Edit: you can also call R8 directly from your Gradle scripts if you prefer as shown in [this repo](https://github.com/ephemient/utf-8b/blob/e44560e3b24a24c48942ecc59d84e5fdc6c547a0/build.gradle.kts#L62) from `@ephemient` )

The rest of this article goes through the process of setup up GR8 for a fictional `com.example` plugin using Kotlin 1.5.

### Applying the `GR8` plugin

Applying the [GR8 plugin](https://github.com/GradleUp/gr8) is similar to any other plugins:

```kotlin
plugins {
  id("org.jetbrains.kotlin.jvm").version(kotlinVersion)
  id("java-gradle-plugin")
  // You can use `kotlin-dsl`too, it's going to set apiLevel="1.4" automatically
  id("kotlin-dsl")
  id("com.gradleup.gr8").version("0.11.2")
}
```

Create a `"shadowedDependencies"` configuration that will contain all the dependencies to shadow (including `kotlin-stdlib.jar`):

```kotlin
val shadowedDependencies = configurations.create("shadowedDependencies")
```

Create a separate `"compileOnlyDependencies"` to resolve the `compileOnly` dependencies (without the other one, like `compileClasspath` does):

```kotlin
val compileOnlyDependencies: Configuration = configurations.create("compileOnlyDependencies") {
  attributes {
    attribute(Usage.USAGE_ATTRIBUTE, project.objects.named<Usage>(Usage.JAVA_API))
  }
}
compileOnlyDependencies.extendsFrom(configurations.getByName("compileOnly"))
```

Declare your dependencies:

```kotlin
dependencies {
  // Add gradleApi() as a compile-only dependency, not shadowed
  add("compileOnly", gradleApi())
  // Alternatively, you can use Nokee distributions
  add("compileOnly", "dev.gradleplugins:gradle-api:7.2")

  // Add dependencies you want to shadow here
  add(shadowedDependencies.name, "com.squareup.okhttp3:okhttp:4.9.0")
  // Add more dependencies...
}
```

Don't forget to remove `kotlin-stdlib` from the default dependencies to avoid having it in the pom file/Gradle module file. In your `gradle.properties` file, add:

```plaintext
kotlin.stdlib.default.dependency=false
```

(See [the Kotlin docs](https://kotlinlang.org/docs/gradle.html#dependency-on-the-standard-library) for more details about `kotlin.stdlib.default.dependency`)

Now configure the `GR8` plugin:

```kotlin
gr8 {
  val shadowedJar = create("default") {
    addProgramJarsFrom(shadowedDependencies)
    addProgramJarsFrom(tasks.getByName("jar"))
    // classpath jars are only used by R8 for analysis but are not included in the
    // final shadowed jar.
    addClassPathJarsFrom(compileOnlyDependencies)

    proguardFile("rules.pro")
  }

  // If you're using the `java-gradle-plugin` plugin. It will add `gradleApi` to the API configuration
  // We don't want that, we want to control what's going out
  removeGradleApiFromApi()

  // Optional: replace the regular jar with the shadowed one in the publication
  replaceOutgoingJar(shadowedJar)

  // Or if you prefer the shadowed jar to be a separate variant in the default publication
  // The variant will have `org.gradle.dependency.bundling = shadowed`
  addShadowedVariant(shadowedJar)

  // Allow to compile the module without exposing the shadowedDependencies downstream
  configurations.getByName("compileOnly").extendsFrom(shadowedDependencies)
  configurations.getByName("testImplementation").extendsFrom(shadowedDependencies)
}
```

That's it for the Gradle configuration! Now you need to tell R8 what to keep and what to relocate. This is done using `rules.pro`

## Configuring R8 rules

This is where things begin to be project specific. If you use reflection or other dynamic features, you might need to fine tune the rules. As a rule of thumbs though, you will always need to keep your plugin public API:

```plaintext
# Keep the API as it's used from build scripts
-keep class com.example.gradle.api.** { *; }
-keep interface com.example.gradle.api.** { *; }
-keep enum com.example.gradle.api.** { *; }
```

Then tell R8 to repackage (relocate) classes:

```plaintext
-repackageclasses com.example.relocated

# Help the relocation process by allowing to change the visibility of some members
-allowaccessmodification
```

Some helpful options:

```plaintext
# Ignore warnings for all the compileOnly dependencies that we didn't pass to R8
-ignorewarnings

# Makes it easier to debug on MacOS case-insensitive filesystem when unzipping the jars
-dontusemixedcaseclassnames

# Keep annotation and other things (might be overkeeping a bit but that's without consequences on the relocation itself)
-keepattributes Signature,Exceptions,*Annotation*,InnerClasses,PermittedSubclasses,EnclosingMethod,Deprecated,SourceFile,LineNumberTable
```

That's the minimal set of rules. Depending on what your plugin uses, you will most likely need some other ones.

### A note about `kotlin.Metadata`

An interesting question is whether to relocate `kotlin.Metadata` or not. The compiler uses `kotlin.Metadata` at compile time. That enables a lot of Kotlin-only features like extension functions, top-level functions, named parameters, default parameters, typealiases, properties, etc... If you relocate them, the compiler will miss a lot of information and fail to compile for things like top-level functions:

```plaintext
// build.gradle.kts
import com.example.gradle.api.someTopLevelFunction

// Unresolved reference: someTopLevelFunction
someTopLevelFunction()

// Default parameters, type aliases, etc... also won't compile
```

If your public API uses a lot of Kotlin features, and if you want your users to be able to use them, keep `kotlin.Metadata`:

```plaintext
// Keep metadata used by the compiler
-keep class kotlin.Metadata { *; }
```

Of course, that's taking the risk that a future version of kotlin changes the definition of `kotlin.Metadata` and overrides that annotation. I'm not 100% sure what would happen there but hopefully it shouldn't happen too much. And if it does happen, most likely other things will break.

If you're keeping `kotlin.Metadata`, you'll also need to keep `kotlin.Unit`:

```plaintext
// The compiler also uses Unit
-keep class kotlin.Unit { *; }
```

`kotlin.Unit` is a special value to the Kotlin compiler and if you relocated it to say, `com.example.relocated.aa`, a runtime error will happen on void methods because the bytecode references a method that returns `com.example.relocated.aa` instead.

### Profit!

Run `./gradlew assemble` to build the shadowed jar. It will be available in

```plaintext
build/gr8/shadow/projectName-version-shadowed.jar
```

In order to verify that your classes were repackaged correctly, unzip the jar. Most of the classes should be under `com/example/relocated`. If not, iterate on the `rules.conf` to allow more relocations. Make sure to also test your plugin to make sure runtime reflexive accesses are still working.

If everything works, congrats! You can now use Kotlin 1.5 and all its APIs in your Gradle plugin! To see it in action, check [the matching PR in apollo-android](https://github.com/apollographql/apollo-android/pull/3542/)

### Should I use this in production?

That's always the million dollar question. I'll give the usual answer of "it depends" 🙃. This is all wildly experimental so come prepared for some hickups. Relocation is always fragile as you don't find issues until runtime. Also, running R8 takes some time. If you need to do this while debugging, that can become annoying.

All that being said, if you have a good test suite and it's working for you, you can actually make it a lot easier to consume your plugins.

## Moving forward

We've seen that R8 gives you a lot of flexibility to shadow, and even shrink/optimize your Gradle plugins. It has a lot of advantages like avoiding dependencies conflicts, allow to use newer Kotlin APIs as well as making self-contained Gradle plugins. It is an effective solution to shipping plugins that use latest Kotlin APIs today. It also has drawbacks as the configuration is not straightforward and reflective accesses require extra care.

Another important drawback is that this requires more resources. If every plugin starts shadowing all their dependencies, it means loading the Kotlin stdlib N times, loading okio P times, etc... That's a lot of classes loaded in the JVM. All of these add up and will take more memory and make your builds slower.

As a wrap-up from this long post, please take the time to upvote https://github.com/gradle/gradle/issues/16345 to prioritize removing the Kotlin stdlib fixed runtime limitation in Gradle. If you're a plugin consumer, move `buildSrc` and rootProjects `buildscript {}` to [convention plugins](https://developer.squareup.com/blog/herding-elephants/) and hopefully one day we'll have Gradle plugin that can share their dependencies \\o/.

Thanks for making it through! Have a wonderful day/evening/night!

\[^1\]: Actually that's not entirely true as the `plugins {}` block is a special block that doesn't allow all the Kotlin syntax so maybe it could have a special handling 🤷‍♂️

\[^2\]: This is not entirely true either 😅. In most cases, the compiler will just optimize the constant value, or use the 1.4 experimental `lowercase` but that was a nice example for a relatively simple and famous 1.5 API.

🙏 Many Thanks to [LouisCAD](https://blog.louiscad.com/) for proofreading this article.

Cover Picture: [Chiesetta sul Col del Nivolet](https://flic.kr/p/ahAszj) by [BORGHY52](https://www.flickr.com/photos/53191561@N03/)
