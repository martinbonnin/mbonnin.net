---
title: 'How Gradle compiles your build scripts'
excerpt: '...'
publishDate: 2022-11-18T17:14:29.144Z
image: '~/assets/images/2022-11-18_how-gradle-compiles-your-build-scripts/jEJIB8e_7.png'
---
_This post is inspired by a [discussion on the Gradle community slack](https://linen.dev/s/gradle-community/t/5100108/are-the-rules-for-how-gradle-parses-compiles-buildscript-and). Many thanks to `@Vampire` and `@ephemient` for their help understanding all of this_

Have you ever tried to do something like this?

```kotlin
val kotlinVersion = "1.7.21"

plugins {
    id("org.jetbrains.kotlin.jvm").version(kotlinVersion)
}

dependencies {
    implementation("org.jetbrains.kotlin:kotlin-stdlib:$kotlinVersion")
}
```

Looks pretty neat, right? Your Kotlin version is defined in a single place and it's easy to change it when a new version is release.

If you have tried this, you probably know it doesn't work. You'll get hit pretty quickly by this:

```
e: build.gradle.kts:4:44: Unresolved reference: kotlinVersion
```

That's surprising. There are very good reasons for this but they're not obvious at first sight.

Let's dive in.

## Plugins and classpaths

Gradle support [plugins](https://docs.gradle.org/current/userguide/plugins.html). Plugins are very handy because they allow you augment your builds. If you're an Android developer, you're certainly familiar with snippets like this:

```kotlin
android {
    compileSdk = 32

    defaultConfig {
        applicationId = "com.example"
        minSdk = 23
        targetSdk = 32
        versionCode = 1
        versionName = "1.0"
    }
}
```

Looking a bit closer, this is all compiled and typesafe. Gradle knows `compileSdk` is a `var Int`, same for `minSdk`, `targetSdk` and others.

This means that Gradle knows about `com.android.build.api.dsl.CommonExtension` the class that defines `compileSdk`. Since Gradle cannot put the whole world on the build script classpath, this has to be conveyed somehow. This is what `plugins {}` do.

## Multiple passes of compilation

Gradle parses your `build.gradle.kts` file and extracts the `plugins {}` block. It does so [using the same KotlinLexer](https://github.com/gradle/gradle/blob/005cceed4ce15708888824566ef94aede20b11c7/subprojects/kotlin-dsl/src/main/kotlin/org/gradle/kotlin/dsl/execution/Lexer.kt#L223) that the Kotlin compiler uses. Once the `plugins {}` block extracted, Gradle compiles it and runs it. This is also the moment when generated accessors are ... well... generated!

So after the `plugins {}` block is evaluated, Gradle has:

* the plugins used by the script and their matching jar
* generated accessors

In a second pass, it can compile and evaluate the script, with all the plugin jars on the classpath. It all makes sense!

This first pass is why the syntax of the `plugins {}` block is so [constrained](https://docs.gradle.org/current/userguide/plugins.html#sec:constrained_syntax).

## It's not only plugins {}

`plugins {}` is the most used block but this also applies to other blocks:

* `buildscript {}`
* `pluginManagement {}`
* `iniscript {}`

If you bump into errors, double check what block you're in. Chances are that your code is evaluated in a separate context.

## What's working

Once we know that, how do we make the above work? In general, I'm not 100% sure what syntax is allowed or not in these blocks. The good news is that there are multiple solutions to define your Kotlin version in a single place (or do other things).

The most straightforward is to use [version catalogs](https://docs.gradle.org/current/userguide/platforms.html):

```toml
// libs.versions.toml
[versions]
kotlin = "1.7.21"

[libraries]
kotlin-stdlib = { group = "org.jetbrains.kotlin", name = "kotlin-stdlib", version.ref = "kotlin" }

[plugins]
kotlin = { id = "org.jetbrains.kotlin.jvm", version.ref = "kotlin" }
```

```kotlin
// build.gradle.kts
plugins {
    alias(libs.plugins.kotlin)
}

dependencies {
    implementation(libs.kotlin.stdlib)
}
```

There are other solutions [using `pluginManagement` and Gradle properties](https://gist.github.com/martinbonnin/e6a2af4a9e722e93b41ce31bf3ef19d0). Or you can build your own!

In all cases, I hope this post helped you understand how Gradle processes your build script. It's nothing magical!
