---
title: 'The different kotlin-stdlibs explained'
excerpt: 'Not sure you should use kotlin-stdlib-jdk8...'
publishDate: 2019-09-15T00:00:00Z
image: '~/assets/images/2019-09-15_The-different-kotlin-stdlibs-explained/1*GH1uKZMDNnK51Shd1m1faA.jpeg'
---

> **Edit 2022--06--30**: reworked the conclusion to highlight that the Kotlin Gradle plugin now adds the stdlib automatically
> **Edit 2023--01--16** : Kotlin 1.8.0 dropped support for Java 1.6 and 1.7 and therefore [all artifacts are now merged](https://kotlinlang.org/docs/whatsnew18.html#updated-jvm-compilation-target)

I love Kotlin as it's a concise yet powerful language with very sensible defaults and design decisions. In that regard, it adopts the Zen of Python:

> There should be one-- and preferably only one --obvious way to do it.

One area where this failed though is the configuration of the stdlib. This is kind of ironic as it's also one of the first thing you configure as a Kotlin newcomer.

What's the best between the below? And what should you choose on an Android device with partial Java 8 support ?

```kotlin
// so many stdlib to choose from!
implementation("org.jetbrains.kotlin:kotlin-stdlib-jre8")
implementation("org.jetbrains.kotlin:kotlin-stdlib-jre7")
implementation("org.jetbrains.kotlin:kotlin-stdlib")
implementation("org.jetbrains.kotlin:kotlin-stdlib-jdk8")
implementation("org.jetbrains.kotlin:kotlin-stdlib-jdk7")
```

### kotlin-stdlib-jre7 and kotlin-stdlib-jre8

These are the easy ones. They have been deprecated in favour of their -jdk7 and -jdk8 counterparts 2 years ago so you can just forget about them. This was made to accomodate the java9 module system and more specifically to avoid [split packages](https://www.logicbig.com/tutorials/core-java-tutorial/modules/split-packages.html). You can read the details from the [github commit](https://github.com/JetBrains/kotlin/commit/e253acd5fde5d192e6afaab4f25848b45fe671af) and [release notes](https://kotlinlang.org/docs/reference/whatsnew12.html?_ga=2.11223412.1161135933.1568472079-576268268.1542579028#kotlin-standard-library-artifacts-and-split-packages).

You might see them occasionally. Don't use them.

### kotlin-stdlib, -jdk7 and -jdk8

According to the [Kotlin doc](https://kotlinlang.org/docs/reference/using-gradle.html#configuring-dependencies):

```
The Kotlin standard library kotlin-stdlib targets Java 6 and above. There are extended versions of the standard library that add support for some of the features of JDK 7 and JDK 8. To use these versions, add one of the following dependencies instead of kotlin-stdlib.
```

Indeed, if you look at the [kotlin-stdlib-jdk7 pom file](https://repo.maven.apache.org/maven2/org/jetbrains/kotlin/kotlin-stdlib-jdk7/1.3.50/kotlin-stdlib-jdk7-1.3.50.pom), you can see that it transitively depends on kotlin-stdlib:

```xml
<dependency>
   <groupId>org.jetbrains.kotlin</groupId>
   <artifactId>kotlin-stdlib</artifactId>
   <version>1.3.50</version>
   <scope>compile</scope>
</dependency>
```

If you include kotlin-stdlib-jdk7, it will pull kotlin-stdlib.

If you include kotlin-stdlib-jdk8, it will pull kotlin-stdlib-jdk7 and kotlin-stdlib. You can also check that by running `./gradlew :dependencies`:

```
compileClasspath - Compile classpath for compilation 'main' (target  (jvm)).
\--- org.jetbrains.kotlin:kotlin-stdlib-jdk8:1.3.50
     +--- org.jetbrains.kotlin:kotlin-stdlib:1.3.50
     |    +--- org.jetbrains.kotlin:kotlin-stdlib-common:1.3.50
     |    \--- org.jetbrains:annotations:13.0
     \--- org.jetbrains.kotlin:kotlin-stdlib-jdk7:1.3.50
          \--- org.jetbrains.kotlin:kotlin-stdlib:1.3.50 (*)
```

We can also check the sizes on [mavenCentral](https://proandroiddev.com/publishing-a-maven-artifact-1-3-glossary-bc0068a440e0) (<https://repo.maven.apache.org/maven2/org/jetbrains/kotlin/>):

```shell
martin@bowser-castle$ ls -al kotlin-stdlib-*.jar
```

```
1326269 Sep 14 16:58 kotlin-stdlib-1.3.50.jar
   3129 Sep 14 16:58 kotlin-stdlib-jdk7-1.3.50.jar
  15476 Sep 14 16:58 kotlin-stdlib-jdk8-1.3.50.jar
```

kotlin-stdlib is 1MB+ while the other two are a few kB at most. That confirms that most of the functionnality is in kotlin-stdlib with additions in -jdk7 and -jdk8.

So let's pull kotlin-stdlib-jdk8 and we'll have everything, right ? Well... not so sure, let's look at what's inside these artifacts.

### kotlin-stdlib

Contains:

- most of the functionality: Collections, Ranges, Math, Regex, File extensions, Locks, etc... Most of what you use daily is in kotlin-stdlib.

### kotlin-stdlib-jdk7

Contains:

- Reflection-free suppressed exceptions

[Suppressed exception](https://docs.oracle.com/javase/tutorial/essential/exceptions/tryResourceClose.html#suppressed-exceptions) were added in Java 7 at the same time as try-with-resources. It gives more information when an exception is thrown while releasing a resource:

```kotlin
val closeable = object: Closeable {
    override fun close() {
        throw Exception("exception from close")
    }
}

closeable.use {
    throw Exception("exception from use")
}
// Java6:
// Exception in thread "main" java.lang.Exception: exception from use
//    at com.example.MainKt.main(Main.kt:13)


// Java7 +:
//
// Exception in thread "main" java.lang.Exception: exception from use
// at MainKt.main(Main.kt:11)
// at MainKt.main(Main.kt)
// Suppressed: java.lang.Exception: exception from close
//    at MainKt$main$closeable$1.close(Main.kt:6)
//    at kotlin.io.CloseableKt.closeFinally(Closeable.kt:56)
//    at MainKt.main(Main.kt:10)
//    ... 1 more

```

kotlin-stdlib supports this [with reflection](https://github.com/JetBrains/kotlin/blob/65244b4bea81f737466618927d4f3afe339cad0d/libraries/stdlib/jvm/src/kotlin/internal/PlatformImplementations.kt#L25) on Java 7+.

kotlin-stdlib-jd7 does the same [without reflection](https://github.com/JetBrains/kotlin/blob/042a8ff6a2cadd8c2e8c156970283d4a28609549/libraries/stdlib/jdk7/src/kotlin/internal/jdk7/JDK7PlatformImplementations.kt#L22).

- [AutoCloseable.use{}](https://github.com/JetBrains/kotlin/blob/e253acd5fde5d192e6afaab4f25848b45fe671af/libraries/stdlib/jdk7/src/kotlin/AutoCloseable.kt#L34)

In addition to the Closeable type, Java 7 introduces [AutoCloseable](https://docs.oracle.com/javase/7/docs/api/java/lang/AutoCloseable.html). kotlin-stdlib-jdk7 adds the `use` extension function on this type as well.

### kotlin-stdlib-jdk8

Contains:

- Java 8 stream extensions

kotlin-stdlib-jdk8 adds extension functions to convert from [java.util.Stream](https://docs.oracle.com/javase/8/docs/api/java/util/stream/package-summary.html) to kotlin.sequences.Sequence and kotlin.collections.List ([source](https://github.com/JetBrains/kotlin/blob/e3883d8d6ddd609e8c0d2ae9af9ab6fb1059dd36/libraries/stdlib/jdk8/src/kotlin/streams/Streams.kt))

- Duration extensions

kotlin-stdlib-jdk8 adds extension functions to convert to/from java.time.Duration and kotlin.time.Duration ([source](https://github.com/JetBrains/kotlin/blob/ff9d2744ce9b63321504cb70cf500bb99bc59f75/libraries/stdlib/jdk8/src/kotlin/time/DurationConversions.kt#L22))

- Named groups in regular expressions

kotlin-stdlib-jdk8 adds support for [named groups](https://www.regular-expressions.info/named.html).`(?<name>group)` will capture the match of group under the backreference "name".

```kotlin
val matchResult = Regex("(?<key>.*)=(?<value>.*)").matchEntire("jdk=8")

if (matchResult != null) {
    println("key=${matchResult.groups.get("key")!!.value}")
}
```

Note that while named groups [started on Java 7](https://docs.oracle.com/javase/7/docs/api/java/util/regex/Matcher.html#group%28java.lang.String%29), the implementation was [not complete until Java 8](https://youtrack.jetbrains.com/issue/KT-12753).

- Support for [ThreadLocalRandom](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/ThreadLocalRandom.html)

kotlin-stdlib-jdk8 will default to ThreadLocalRandom for [Random.Default](https://github.com/JetBrains/kotlin/blob/695d657ca88faf42d56917cf60619aaea5035407/libraries/stdlib/src/kotlin/random/Random.kt#L242). This should remove some contention in multi-threaded scenarios ([stackoverflow](https://stackoverflow.com/questions/23396033/random-over-threadlocalrandom)) although there's a fallback on Java 6\&7 that uses ThreadLocal to emulate a ThreadLocalRandom. Again, ThreadLocalRandom also started on Java 7 but [was buggy](https://github.com/JetBrains/kotlin/commit/042a8ff6a2cadd8c2e8c156970283d4a28609549) so it is only added for Java 8.

### What to use on Android ?

Each time, -jdk7 and -jdk8 artifacts add a combination of PlatformImplementations and extension functions. But what is really used on a device ?

My pixel 3 reports `System.getProperty("java.specification.version")="0.9"`. 0.9 is below Java 7. I'm not even sure it matches Java 6. Also,`System.getProperty("java.vm.name")` returns `"Dalvik"`. So it looks like this is reporting some custom Android VM.

This is not picked up by the stdlib at runtime. That means whatever artifact you put in the classpath, the stdlib is always going to fallback to the default [PlatformImplementations](https://github.com/JetBrains/kotlin/blob/65244b4bea81f737466618927d4f3afe339cad0d/libraries/stdlib/jvm/src/kotlin/internal/PlatformImplementations.kt#L57).

```kotlin
// https://github.com/JetBrains/kotlin/blob/65244b4bea81f737466618927d4f3afe339cad0d/libraries/stdlib/jvm/src/kotlin/internal/PlatformImplementations.kt#L42
internal val IMPLEMENTATIONS: PlatformImplementations = run {
    val version = getJavaVersion()
    if (version >= 0x10008) {
        try {
            return@run castToBaseType<PlatformImplementations>(Class.forName("kotlin.internal.jdk8.JDK8PlatformImplementations").newInstance())
        } catch (e: ClassNotFoundException) { }
        try {
            return@run castToBaseType<PlatformImplementations>(Class.forName("kotlin.internal.JRE8PlatformImplementations").newInstance())
        } catch (e: ClassNotFoundException) { }
    }

    if (version >= 0x10007) {
        try {
            return@run castToBaseType<PlatformImplementations>(Class.forName("kotlin.internal.jdk7.JDK7PlatformImplementations").newInstance())
        } catch (e: ClassNotFoundException) { }
        try {
            return@run castToBaseType<PlatformImplementations>(Class.forName("kotlin.internal.JRE7PlatformImplementations").newInstance())
        } catch (e: ClassNotFoundException) { }
    }

    PlatformImplementations()
}
```

With Android supporting java.time.Duration with API level 26+ and the Stream API with API level 24+ ([doc](https://developer.android.com/studio/write/java8-support)), that means:

- jdk8 ThreadLocalRandom won't be used on any API level.
- jdk8 Named groups will throw at runtime on all API levels.
- jdk8 Duration extensions will work on API level 26+.
- jdk8 Stream extensions will work on API level 24+.
- jdk7 reflection-free suppressed exceptions won't be used on any API level.

Duration extensions are literally [two lines of experimental code](https://github.com/JetBrains/kotlin/blob/ff9d2744ce9b63321504cb70cf500bb99bc59f75/libraries/stdlib/jdk8/src/kotlin/time/DurationConversions.kt). Stream extensions are a bit more but if you're using Kotlin, you can (and certainly should) replace them with sequences or collections anyway.

On the other hand, depending on kotlin-stdlib-jdk8 adds the JDK7/JDK8PlatformImplementations code. Granted it's not huge but R8 won't be able to strip it as it's used at runtime depending on a Java specification version that seems to be always be 0.9 on Android.

### Conclusion

All thing considered, **the regular kotlin-stdlib seems like the best candidate on Android**. Since most of the features in -jdk7 and -jdk8 are not accessible, it avoids downloading extra artifacts and loading extra bytecode. That seems a bit counter-intuitive though as I would have expected the opposite.

Note that if you're using Kotlin 1.4+, the [Kotlin Gradle Plugin now adds the](https://kotlinlang.org/docs/whatsnew14.html#dependency-on-the-standard-library-added-by-default)[-](https://kotlinlang.org/docs/whatsnew14.html#dependency-on-the-standard-library-added-by-default)`jdk8`[stdlib by default](https://kotlinlang.org/docs/whatsnew14.html#dependency-on-the-standard-library-added-by-default). If you want to opt-out, you can opt-out in `gradle.properties` with `kotlin.stdlib.default.dependency=false` .

What do you use? Please let me know before I remove all jdk8 from my projects!

Photo: "I heart coffee" by [jojo 77](https://flic.kr/p/8xYHYZ)

By [Martin Bonnin](https://medium.com/@mbonnin) on [September 15, 2019](https://medium.com/p/83d7c6bf293).

[Canonical link](https://medium.com/@mbonnin/the-different-kotlin-stdlibs-explained-83d7c6bf293)

Exported from [Medium](https://medium.com) on November 9, 2024.
