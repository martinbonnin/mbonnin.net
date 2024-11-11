---
title: 'Gradle brainteasers 1/2: aggregating artifacts'
excerpt: 'Fun times with project isolation and dependency resolution...'
publishDate: 2024-07-15T10:44:26.305Z
image: '~/assets/images/2024-07-15_gradle-brainteasers-12-aggregating-artifacts/c6a866b4-e512-483d-8e3a-decefe9261c9.webp'
---

I've been developing Gradle plugins for 7 years now. Sometimes [I love it](https://github.com/GradleUp/gratatouille), sometimes [I hate it](https://mbonnin.medium.com/actual-footage-of-different-kinds-of-gradle-configurations-9678bd681793). But even when I hate it, I love hating it!

I just realized some of the Gradle APIs are like those metal wire brain teasers games:

- Are they easy? No.

- Do you have to turn them upside down for hours (or months...) trying to understand what you're supposed to do? Yup, most probably.

- Do you get a nice feeling of completion once you figure out how to untangle them? Absolutely!

I just had a couple of "Aha!" moment very recently. This post is about the "Aha!" moment of untangling dependency resolution and project isolation.  
A follow up one will be about input files.  
Warning, **spoilers ahead**, **do not read if you want to play the game yourself.**

# The problem

If you have a multi-project build, there are a number of occasions where aggregating artifacts is desirable. Dokka [is an example](https://github.com/Kotlin/dokka?tab=readme-ov-file#get-started-with-dokka). Maven publication is another one. Each project ([also known as module](https://github.com/autonomousapps/gradle-glossary/blob/main/README.asciidoc#module)) creates their artifacts and you want to collect them in the root project to upload everything all at once.

```kotlin
# aggregate all publications accross all modules and publish them
# to the Maven Central Portal
./gradlew publishToMavenCentral
```

Sounds easy, right?

Well... Not that much. There are a lot of traps along the way.

# Project isolation

[Project isolation](https://docs.gradle.org/current/userguide/isolated_projects.html) is an initiative to make builds faster by parallelizing the creation of the task graph. You enable it with the `Dorg.gradle.unsafe.isolated-projects` flag.

Up until recently it wasn't really an option to enable it but it's been [picking](https://youtrack.jetbrains.com/issue/KT-54105) [up](https://github.com/google/ksp/issues/1943) [steam](https://github.com/gradle/gradle/issues/29045) lately!

Let's take a simple build:

!\[\](https://cdn.hashnode.com/res/hashnode/image/upload/v1721041049710/41cedb0a-984e-4d81-83a1-c1aa9adfc19b.png align="center")

By using project isolation, building the task graph for project1 and project2can be executed in parallel. That's right, actually using all the CPUs in your machine 🎉.

<div data-node-type="callout">
<div data-node-type="callout-emoji">💡</div>
<div data-node-type="callout-text">Project isolation is about building <strong>the task graph</strong> in parallel, not executing the tasks in parallel, which is already possible.</div>
</div>

If you've read [the documentation about sharing outputs between projects](https://docs.gradle.org/current/userguide/cross_project_publications.html), you know that you shouldn't do things like this:

```kotlin
// build.gradle.kts
dependencies {
   // Don't do this!
   add("aggregate", project(":project1").tasks.named("generatePublication")
}
```

From the documentation:

> This publication model is _unsafe_ and can lead to non-reproducible and hard to parallelize builds.

If the projects are evaluated concurrently then accessing the mutable `Project.tasks` is prone to race conditions.

If we want to support project isolation, we need to do this instead in our root (consumer) project:

```kotlin
// build.gradle.kts
dependencies {
   // Do this
   // This is project isolation compatible
   // (PS: this doesn't use attributes for REASONs!)
   add("aggregate", project(":project1", "outgoingPublication")
}
```

<div data-node-type="callout">
<div data-node-type="callout-emoji">ℹ</div>
<div data-node-type="callout-text"><code>"outgoingPublication"</code> is the name of an <a target="_blank" rel="noopener noreferrer nofollow" href="https://docs.gradle.org/current/userguide/variant_model.html#outgoing_variants_report" style="pointer-events: none">outgoing configuration</a> exposing all our files.</div>
</div>

To expose the artifacts in our producer project, we use configurations and the artifacts {} API:

```kotlin
// project1/build.gradle.kts
val configuration = configurations.consumable("outgoingPublication").get()

val m2Dir = layout.buildDirectory.dir("m2/").get()
publishing {
  // Add a local repository
  repositories {
    maven {
      name = "m2"
      setUrl(uri(m2Dir.asFile.path))
    }
  }
}
artifacts {
  artifacts {
    // expose the repository to other projects
    add(configuration.name, m2Dir) {
      builtBy("publishAllPublicationsToM2Repository")
    }
  }
}
```

(There's a lot in there and if you're curious about how that works in details, take a look at [this other post about Gradle configurations)](https://mbonnin.medium.com/actual-footage-of-different-kinds-of-gradle-configurations-9678bd681793).

Using the configurations and artifacts API, we can express cross-project dependencies. But it's a bit verbose.

# Avoiding repetition

The above works fine but assuming you have 50 modules, you now have to do something like this:

```kotlin

// build.gradle.kts
dependencies {
   add("aggregate", project(":project1", "outgoingPublication")
   add("aggregate", project(":project2", "outgoingPublication")
   // ...
   // Pfewwwww, that's a long list of projects to maintain
   add("aggregate", project(":project50", "outgoingPublication")
}
```

Wouldn't it be nice if instead we could register the dependency automatically? After all, the subprojects have some build logic that runs already. Could they automatically register themselves as dependencies of the root project?

To this day I haven't found a way to add cross-project dependencies in a project isolation compatible way ([Gradle issue](https://github.com/gradle/gradle/issues/29037)).

But luckily there is another solution!

# Lenient artifact views

The trick is in using `subprojects` and [lenient artifact views](<https://docs.gradle.org/current/javadoc/org/gradle/api/artifacts/ArtifactView.ViewConfiguration.html#lenient(boolean)>):

```kotlin
// Create the configuration
val aggregate = configurations.create("aggregate")
// Add all subprojects as dependency
// ℹ️ subprojects {} is not PI compatible
// (but subprojects.forEach {} is)
subprojects.forEach {
  aggregate.dependencies.add(
    dependencies.project(":${it.name}", "outgoingPublication")
  )
}

tasks.register("zipAggregate", Zip::class.java) {
  // Use a lenient artifact view to avoid failing if some subprojects
  // do not publish anything.
  from(aggregate.incoming.artifactView { lenient(true) }.files.asFileTree)
  destinationDirectory.set(layout.buildDirectory.dir("zip"))
  archiveBaseName.set("aggregate")
}
```

<div data-node-type="callout">
<div data-node-type="callout-emoji">💡</div>
<div data-node-type="callout-text"><em>Note how this leverages the </em><code>FileCollection</code><em>and </em><code>asFileTree</code><em>APIs, which will be the topic of the next post.</em></div>
</div>

By using a lenient artifact view, the root project can still collect all subprojects. Because the dependency is added on the explicit `"outgoingPublication"` configuration, there is no risk of resolving other (wrong) artifacts. And because the resolution is lenient, it will fail silently if a project doesn't publish anything. **SUCCESS!**

!\[A metal wire brain teaser game. The two parts are sitting aside on a wooden table.\](https://cdn.hashnode.com/res/hashnode/image/upload/v1720982965178/f5f6ca6a-6e6a-4baa-90a7-c868f86ed984.webp align="center")

# Wrap-up

I've been toying with publishing and Maven Central APIs [for a while now](https://github.com/martinbonnin/vespene). Project isolation was something that has been itching me for the last 6 months or so.  
Using lenient artifact views provides a simple solution that would otherwise require a lot of fragile code.

With this itch gone, new opportunities for publishing arise, stay tuned!

---

_PS: this only works for cases where a single root projects depends on all the other ones but modeling a more complex project graph is still itching me..._

_Brainteasers pictures from_ [_mtairymd_](https://www.instructables.com/member/mtairymd/) _on_ [_Instructables_](https://www.instructables.com/Metal-Wire-Puzzle-Solutions/)
