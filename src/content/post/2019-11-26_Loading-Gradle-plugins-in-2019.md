---
title: 'Loading Gradle plugins in 2019'
excerpt: 'Three different ways to load your Gradle plugins and a few ways to apply them....'
publishDate: 2019-11-26T00:00:00Z
image: '~/assets/images/2019-11-26_Loading-Gradle-plugins-in-2019/1*qwUkdUbPFPpWxMQ0RkB0rw.jpeg'
---

As an Android developer, I use a bunch of Gradle plugins: the Android Gradle plugin and a few other helpful ones too like Kotlin, Fabric, Dokka, SqlDelight, etc..

Most of the time, I copy/paste the instructions from the installation notes. For an example, the traditional way of adding a Gradle plugin to your build:

```groovy
// build.gradle
buildscript {
  repositories {
    google()
  }

  dependencies {
    // add the plugin to the build classpath
    classpath("com.android.tools.build:gradle:3.5.2")
  }
}

// app/build.gradle
// apply it to the project
apply plugin: 'com.android.application'
```

While this still works, there are nowadays a few other options that give better tooling or enable new features, and it's safe to say the above shouldn't be recommended anymore.

### TLDR;

If you're in a hurry, and you use buildSrc, do this:

```kotlin
// buildSrc/build.gradle.kts

repositories {
  mavenCentral()
  google()
}

dependencies {
  // add all your plugins artifacts here
  classpath("com.android.tools.build:gradle:3.5.2")
  classpath("com.squareup.sqldelight:gradle-plugin:1.2.0")
  // ...
}

// build.gradle.kts

plugins {
  // load the plugins but do not apply them to the root project
  id("com.android.application").apply(false)
  id("com.squareup.sqldelight").apply(false)
}

// app/build.gradle.kts

plugins {
  // ... 
  id("com.android.application")
}

// lib/build.gradle.kts

plugins {
  // ... 
  id("com.squareup.sqldelight")
}
```

If you're in a hurry, and you don't use buildSrc:

```kotlin
// settings.gradle.kts

pluginManagement {
    repositories {
        mavenCentral()
        google()
    }
    plugins {
        id("com.android.application").version("3.5.2")
        id("com.squareup.sqldelight").version("1.2.0")
        id("org.jetbrains.kotlin.android").version("1.3.60")
    }
    resolutionStrategy {
        // These plugins don't have a marker artifact, tell gradle were to look them up
        eachPlugin {
            if (requested.id.id == "com.android.application") {
                useModule("com.android.tools.build:gradle:${requested.version}")
            }
            if (requested.id.id == "com.squareup.sqldelight") {
                useModule("com.squareup.sqldelight:gradle-plugin:${requested.version}")
            }
            // The kotlin plugins have marker artifacts so we don't need to handle 
            // them in resolutionStrategy {}
        }
    }
}

// app/build.gradle.kts

plugins {
    // ... 
    id("com.android.application")
}

// lib/build.gradle.kts

plugins {
    // ... 
    id("com.squareup.sqldelight")
}
```
If you have a few minutes, read on 📚!

### Anatomy of a Gradle plugin

A plugin is a simple jar file containing JVM class files. It's like a java library or executable jar except the entry point, instead of being `main()` is a class that can be applied to a `Project` :

```kotlin
package com.example

class GreetingPlugin : Plugin<Project> {
    override fun apply(project: Project) {
        project.task("hello") {
            doLast {
                println("Hello from the GreetingPlugin")
            }
        }
    }
}
```

Another important thing about this jar file is that it needs to contain a special resource file named `com.example.greeting.properties` in the `META-INF.gradle-plugins` folder. `com.example.greeting` is the pluginId and allows to lookup the entry point class (`com.example.GreetingPlugin` here).

```
// src/main/resources/META-INF.gradle-plugins/com.example.greeting.properties
implementation-class=com.example.GreetingPlugin
```

In the case of the Android plugin:

* `classpath("com.android.tools.build:gradle:3.5.2")` tells Gradle to download the [jar](https://dl.google.com/dl/android/maven2/com/android/tools/build/gradle/3.5.2/gradle-3.5.2.jar) from the [Google maven repo](https://maven.google.com/web/index.html) and load it in the build in the classpath.
* `apply plugin: 'com.android.application'` tells gradle to look for a [com.android.application.properties](https://android.googlesource.com/platform/tools/base/+/ecdfaee5fbdfa69e82bb9266b6742d9c3db27880/build-system/gradle-core/src/main/resources/META-INF/gradle-plugins/com.android.application.properties) resource file, create a new instance of [AppPlugin](https://android.googlesource.com/platform/tools/base/+/ecdfaee5fbdfa69e82bb9266b6742d9c3db27880/build-system/gradle-core/src/main/java/com/android/build/gradle/AppPlugin.kt) and apply it to the project.

Two pluginIds can point to the [same artifact and class](https://github.com/JetBrains/kotlin/tree/b37dc32e0383998e12c91af45d8726f2126c3072/libraries/tools/kotlin-gradle-plugin/src/main/resources/META-INF/gradle-plugins).For an example, the below are mostly equivalent:

* `apply plugin:kotlin`
* `apply plugin: org.jetbrains.kotlin.jvm`

Also, an artifact can contain several pluginIds. For an example, the Android artifact [defines plugins](https://android.googlesource.com/platform/tools/base/+/ecdfaee5fbdfa69e82bb9266b6742d9c3db27880/build-system/gradle-core/src/main/resources/META-INF/gradle-plugins) for:

* com.android.application
* com.android.library
* com.android.instantapp
* etc..

### Applying plugins: the plugins {} block

The plugin {} block is now the official way to apply plugins to your build. From the [documentation](https://docs.gradle.org/5.6.3/userguide/plugins.html#sec:plugins_block):

```
This allows Gradle to do smart things such as:
* Optimize the loading and reuse of plugin classes
* Allow different plugins to use different versions of dependencies.
* Provide editors detailed information about the potential properties and values in the buildscript for editing assistance.
```

In particular, this allows the Kotlin DSL to generate [typesafe accessors](https://docs.gradle.org/current/userguide/kotlin_dsl.html#type-safe-accessors) for your build scripts.

Applying plugins with the plugins {} block is as easy as specifying their pluginId:

```kotlin
plugins {
  id("org.jetbrains.kotlin.android").version("1.3.60")
}
```

You can use the plugin block in your module build script, in the root build script but the versions should all match. You cannot load two plugins with different versions. To do this, load all your plugins in your root build.gradle file withtout applying them:

```kotlin
// build.gradle.kts
plugins {
  // load the module, do not apply it    
  id("org.jetbrains.kotlin.android").version("1.3.60").apply(false)
}

// module/build.gradle.kts
plugins {
  // this will apply the plugin
  id("org.jetbrains.kotlin.android")
}
```

Latest versions of gradle even allow you to define your plugins in a centralized place in your settings.gradle.kts:

```kotlin
pluginManagement {
  plugins {
   id("org.jetbrains.kotlin.android").version("1.3.60").apply(false)     
  }
}
```

### Loading the plugin artifact in the classpath

The plugin {} block works well if the artifact containing your pluginId is already in the classpath. Most of the time, it's not the case so you need a way to retrieve and load the appropriate maven artifact. Gradle introduced [marker artifacts](https://docs.gradle.org/current/userguide/plugins.html#sec:plugin_markers) to lookup the implementation artifact for a given pluginId. Just like the `com.example.properties` resource file points to the plugin implementation, the `com.example:com.example.gradle.plugin` artifacts points to the actual artifact by depending on it in its pom file.

For an example the [Kotlin marker artifact](https://plugins.gradle.org/m2/org/jetbrains/kotlin/jvm/org.jetbrains.kotlin.jvm.gradle.plugin/1.3.60/)contains this pom:


```xml
<project xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://maven.apache.org/POM/4.0.0" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
<modelVersion>4.0.0</modelVersion>
<groupId>org.jetbrains.kotlin.jvm</groupId>
<artifactId>org.jetbrains.kotlin.jvm.gradle.plugin</artifactId>
<version>1.3.60</version>
<packaging>pom</packaging>
<dependencies>
<dependency>
<groupId>org.jetbrains.kotlin</groupId>
<artifactId>kotlin-gradle-plugin</artifactId>
<version>1.3.60</version>
</dependency>
</dependencies>
</project>
```

This tells gradle that `org.jetbrains.kotlin.jvm`can be found in the artifact `org.jetbrains.kotlin:kotlin-gradle-plugin`. If your plugin is not on the Gradle Plugin Portal, you can still use the plugin {} block by adding a repository to the `pluginManagement {}` block:

```kotlin
pluginManagement {
    repositories {
        // The repo where to look for
        maven {url = uri("https://com.example/m2")}
    }
}
```

And if your plugin does not have a marker artifact, you can also tell Gradle where to look for the artifact:

```kotlin
pluginManagement {
    resolutionStrategy {
        // These plugins don't have a marker artifact, tell gradle were to look them up
        eachPlugin {
            if (requested.id.id == "com.android.application") {
                useModule("com.android.tools.build:gradle:${requested.version}")
            }
            if (requested.id.id == "com.squareup.sqldelight") {
                useModule("com.squareup.sqldelight:gradle-plugin:${requested.version}")
            }
        }
    }
}
```

Using this, you have a centralized way to declare all the plugins your build uses. You can then apply them independently in different modules:

```kotlin
// settings.gradle.kts

pluginManagement {
    repositories {
        mavenCentral()
        google()
    }
    plugins {
        id("com.android.application").version("3.5.2")
        id("com.squareup.sqldelight").version("1.2.0")
        id("org.jetbrains.kotlin.android").version("1.3.60")
    }
    resolutionStrategy {
        // These plugins don't have a marker artifact, tell gradle were to look them up
        eachPlugin {
            if (requested.id.id == "com.android.application") {
                useModule("com.android.tools.build:gradle:${requested.version}")
            }
            if (requested.id.id == "com.squareup.sqldelight") {
                useModule("com.squareup.sqldelight:gradle-plugin:${requested.version}")
            }
            // The kotlin plugins have marker artifacts so we don't need to handle 
            // them in resolutionStrategy {}
        }
    }
}

// app/build.gradle.kts

plugins {
    // ... 
    id("com.android.application")
}

// lib/build.gradle.kts

plugins {
    // ... 
    id("com.squareup.sqldelight")
}
```

This works well as long as you're not using [buildSrc](https://docs.gradle.org/current/userguide/organizing_gradle_projects.html#sec:build_sources)

### Using buildSrc

If your build grows, you can use buildSrc to add some build logic. buildSrc is an included build whose classes are automatically added to the build classpath. That also means that dependencies declared in buildSrc are also added to your build classpath.

The following file will add the android and sqldelight plugins to the build classpath so you can later on apply them from a plugins {} block.

```kotlin
// buildSrc/build.gradle.kts

repositories {
  mavenCentral()
  google()
}

dependencies {
  // add all your plugins artifacts here
  classpath("com.android.tools.build:gradle:3.5.2")
  classpath("com.squareup.sqldelight:gradle-plugin:1.2.0")
  // ...
}
```

This works well except that buildSrc is loaded first and whatever dependencies you declare in your other build scripts will not be loaded as described in this [github issue](https://github.com/gradle/gradle/issues/4741). That can lead to [very weird issues](https://github.com/gradle/gradle/issues/8301). To prevent that from happening, **load all your plugins from buildSrc**. This way, you're guaranteed that you know what version is going to be used.

### Conclusion

That's a lot of different ways to accomplish basically the same thing. Using buildSrc seems to be a trend these days so putting all the plugin dependencies there will definitely avoid some troubles.

If not using buildSrc, the marker artifacts allow for a very concise and elegant syntax. Few projects use them at the moment but it is changing fast!

Happy building !

By [Martin Bonnin](https://medium.com/@mbonnin) on [November 26, 2019](https://medium.com/p/640818be5925).

Photo: Elephant by [designerpoint](https://www.needpix.com/photo/download/1192963/elephant-africa-african-bush-elephant-proboscis-mammal-pachyderm-south-africa-botswana-herd-of-elephants)

[Canonical link](https://medium.com/@mbonnin/loading-gradle-plugins-in-2019-640818be5925)

Exported from [Medium](https://medium.com) on November 9, 2024.
