---
title: 'An unofficial guide to Android Lint'
excerpt: 'Everything about gradle and XML configuration....'
publishDate: 2019-10-20T00:00:00Z
image: '~/assets/images/2019-10-20_An-unofficial-guide-to-Android-Lint/1*e578jPqHJsOAzKQpoq1Emw.jpeg'
---

Android Lint is a great tool to catch structural errors and improve your Android codebase. Unfortunately, the [documentation](https://developer.android.com/studio/write/lint) can be a bit sparse and does not go in the details of precedence and XML options. We'll try to do that here.

### The different flavors of lint

Android lint ([source code](https://android.googlesource.com/platform/tools/base.git/+/refs/heads/mirror-goog-studio-master-dev/lint)) is the engine that performs the check. Its name come from the original 1978 C lint used to analyze C source files. Today lint is the umbrella term for tools analyzing source files and you'll find ESlint, JSlint, pylint and other for other languages. Ktlint is a thing too, which you can read about [there](https://proandroiddev.com/simplify-android-kotlin-code-with-ktlint-20c702108901).

For Android, the lint engine can be invoked in different ways:

1. From the command line (cli): you will find the command under `$ANDROID_HOME/tools/bin/lint`
2. From gradle: `./gradlew :app:lint`.
3. From intelliJ/Android Studio: the suggestions and helpful yellow underlines.

This guide will focus on invoking lint from gradle. IDE/cli are slightly different and will most likely require more configuration and/or not report the same results and I haven't looked into this yet.

### Invoking lint from gradle

You can invoke lint in multiple ways:

1. `./gradlew lint`:will run lint on all modules for all variants.
2. `./gradlew :app:lint`:will run lint on the app module for all variants.
3. `./gradlew :library:lint`:will run lint on the library module for all variants.
4. `./gradlew :app:lintFlavorDebug`:will run lint on the app module the `flavorDebug`variant.

Unless you have a lot of different code in your different flavors, solution 4 will save you some time. You still want lint to check the `library` module too. Too do that, make sure to set `checkDependencies = true` or you will miss some warnings:

```kotlin
android {
    lintOptions {
        isCheckDependencies = true
    }
}
```

### Lint Checks

Lint contains a number of checks for issues that are each identified by an "id". You can get the list by typing `$ANDROID_HOME/tools/bin/lint --show`. (Note how this runs the lint bundled with your Android SDK and not the gradle one, which might be a different version. We will assume they're are not too different for now. Else you can always check the source code in the [google repo](https://android.googlesource.com/platform/tools/base.git/+/refs/heads/mirror-goog-studio-master-dev/lint/libs/lint-checks/src/main/java/com/android/tools/lint/checks/AppLinksAutoVerifyDetector.java#87)).

```
MissingTranslation
------------------
Summary: Incomplete translation

Priority: 8 / 10
Severity: Fatal
Category: Correctness:Messages

If an application has more than one locale, then all the strings declared in
one language should also be translated in all other languages.

If the string should not be translated, you can add the attribute
translatable="false" on the <string> element, or you can define all your
non-translatable strings in a resource file called donottranslate.xml. Or, you
can ignore the issue with a tools:ignore="MissingTranslation" attribute.

By default this detector allows regions of a language to just provide a subset
of the strings and fall back to the standard language strings. You can require
all regions to provide a full translation by setting the environment variable
ANDROID_LINT_COMPLETE_REGIONS.

You can tell lint (and other tools) which language is the default language in
your res/values/ folder by specifying tools:locale="languageCode" for the root
<resources> element in your resource file. (The tools prefix refers to the
namespace declaration http://schemas.android.com/tools.)
```

All issues have:

- An id ("MissingTranslation" here)
- A Severity ("fatal", "error", "warning", "informational" or "ignore")
- A priority between 1 and 10
- A category
- A default state: whether this issue is checked by default or not. Disabled issues will be marked with `NOTE: This issue is disabled by default!`

### Configuration

Lint is highly configurable. The number of options and different combinations is huge. I think one of the keys to understand how configuration happens is to realize that most of parameters are actually stateful and some override each other. The order in which you declare them is important.

Determining exactly what is going to happen with precision will certainly require digging into the [source code](https://android.googlesource.com/platform/tools/base.git/+/67138ae2588344dc333c708b61ea84c57082906c/build-system/gradle-core/src/main/java/com/android/build/gradle/internal/dsl/LintOptions.java). But the below rules should give a good enough approximation for most use cases.

#### Enabling/Disabling checks

```kotlin
lintOptions {
  // disable checks enabled by default
  disable("RtlHardcoded", "RtlCompat")
  // Enable some checks that are disabled by default.
  enable("NegativeMargin", "GoogleAppIndexingApiWarning")
  // Only check this exact list of issues
  // Shorthand for disable(everything) and enable(these issues)
  check("UnusedResources", "DevModeObsolete")
  // Shorthand for enable(allWhereSeverityIsWarning)
  // Severity is resolved at the start of configuration so this will not be affected by
  // other options
  isCheckAllWarnings = true
}
```

#### Controlling severity

```kotlin
lintOptions {
  // You can put severity configuration inside an XML file.
  // Order inside the XML file is important.
  setLintConfig(file("lint.xml"))

  // Change the severity of the passed issueIds.
  // Order is important.
  // This overrides the XML configuration.
  fatal("UnusedResources", "MissingTranslation")
  error("UnusedResources", "MissingTranslation")
  warning("UnusedResources", "MissingTranslation")
  informational("UnusedResources", "MissingTranslation")
  ignore("UnusedResources", "MissingTranslation")

  // turns the severity of all "warning" issues into "ignore"
  // This is applied last and overrides the XML and methods above.
  isIgnoreWarnings = true
  // turns the severity of all "warning" issues into "error"
  // This is applied last andoverrides the XML and methods above.
  isWarningsAsErrors = true

}
```

Controlling severity is more complex. The different options are evaluated in this order:

1. Default severity from lint itself.
2. XML value
3. Individual override from gradle ( `fatal(), error(), ...`)
4. Global override from gradle ( `ignoreWarnings, warningsAsErros, ...`)

#### Other options you should certainly enable

```kotlin
lintOptions {
  // aborts the build if an error is found
  // severity is resolved at execution so once all the rules have been processed
  isAbortOnError = true
  // also check source code from included projects
  isCheckDependencies = true
  // automatically runs lint on release builds. If you run lint from your CI
  // you can disable it here and save some time
  isCheckReleaseBuilds = false
  // also check the test sources
  isCheckTestSources = true
  // also check the generated sources
  isCheckGeneratedSources = true
}
```

#### XML configuration syntax

The [source code](https://android.googlesource.com/platform/tools/base.git/+/67138ae2588344dc333c708b61ea84c57082906c/lint/libs/lint-api/src/main/java/com/android/tools/lint/client/api/DefaultConfiguration.java) gives us some hints of how to write the `lint.xml` file. The order of the nodes is important!

```xml
<lint>

    <issue id="UnusedAttribute" severity="warning">
        <!-- Ignore the specified issue if the location matched this path -->
        <ignore path="**/AndroidManifest.xml"/>
        <!-- Ignore the specified issue if the message or the location matches the regex -->
        <ignore regexp="networkSecurityConfig"/>
        <!-- path takes precedence over regexp so it's no use adding both -->
        <!--<ignore path="**/AndroidManifest.xml" regexp="networkSecurityConfig"/>-->
    </issue>
    <!-- You can also specify a list of ids -->
    <issue id="UnusedAttribute, MissingTranslation" severity="error"/>
    <!-- Nodes overrides the previous ones. UnusedAttribute will become ignored after this -->
    <issue id="UnusedAttribute, MissingTranslation" severity="ignore"/>
    <!-- "all" is a special id that will be used as a fallback for ids that are not defined elsewhere in the
    XML. Putting it last will not overwrite the issues above. Here, we mark any unspecified issue as fatal -->
    <issue id="all" severity="fatal"/>
    <!-- Any number of additional issue nodes -->
    <issue ...
</lint>
```

### Wrapup

Lint is a powerful tool that allows to increase the code quality. The configuration took some time but this is definitely worth it and it has already helped us fix actual bug! I really hope the discrepencies between the IDE and gradle invocation are resolved soon. Then we'll be able to fix warnings even before they reach CI!

Happy lint everyone!

By [Martin Bonnin](https://medium.com/@mbonnin) on [October 20, 2019](https://medium.com/p/188c0654b29b).

Photo: "Library" by [Kotomi\_](https://flic.kr/p/r4TX3R)

[Canonical link](https://medium.com/@mbonnin/an-unofficial-guide-to-android-lint-188c0654b29b)

Exported from [Medium](https://medium.com) on November 9, 2024.
