---
title: 'SemVer is a great versioning scheme for Kotlin libraries'
excerpt: 'Both Maven and Gradle support SemVer'
publishDate: 2026-01-16T00:00:00Z
image: '~/assets/images/2026-01-16-semver-is-great-for-your-kotlin-libraries/thumbnail.jpg'
---

The question came up lately what versioning scheme to use for Kotlin libraries ([KotlinLang slack](https://slack-chats.kotlinlang.org/c/library-development), [Twitter](https://x.com/Sellmair/status/2011086287059751085), [BlueSky](https://bsky.app/profile/mbonnin.net/post/3mcezm43nf326)). 

This is an interesting question, with lots of nuances. 

The closest we have to an authoritative answer is Semantic Versioning (or [SemVer](https://semver.org/)). SemVer defines a [grammar](https://github.com/semver/semver/blob/master/semver.md?plain=1#L147) for version numbers and rules for ordering. SemVer looks like `1.0.0-alpha.1`.

The alternative, used a lot in the ecosystem, is zero-padded versioning. With zero-padded versioning, versions are padded with zeroes to ensure a fixed number of digits and a natural lexicographic order (think filesystem-like). Zero-padded looks like `1.0.0-alpha01`.

I've been wrestling with this question for many years. In fact, I was asking the [same question 5 years ago](https://slack-chats.kotlinlang.org/t/502952/i-see-libs-prefixing-their-alpha-versions-with-0-but-not-doi#ee149f44-ab63-46eb-a590-1a021cb0cf47). At that time, I landed on zero-padded versioning. 

I have changed my mind. This post explains why.

## Two versioning schemes

To make things very explicit, let's take a look at examples of what it looks like in real life.

Both schemes allow a vast range of options, but we'll limit ourselves to alphas, betas, rcs, and stable:

| Zero-padded   | SemVer         |
|---------------|----------------|
| 0.1.0         | 0.1.0          |
| 0.1.1         | 0.1.1          |
| 0.1.10        | 0.1.10         |
| 1.0.0-alpha01 | 1.0.0-alpha.1  |
| 1.0.0-alpha10 | 1.0.0-alpha.10 |
| 1.0.0-beta01  | 1.0.0-beta.1   |
| 1.0.0-beta10  | 1.0.0-beta.10  |
| 1.0.0-rc01    | 1.0.0-rc.1     |
| 1.0.0-rc10    | 1.0.0-rc.10    |
| 1.0.1         | 1.0.1          |
| 1.0.10        | 1.0.10         |
| 1.1.0         | 1.1.0          |
| 2.0.0         | 2.0.0          |
| 10.0.0        | 10.0.0         |


## Maven and Gradle both support SemVer

Versions are important because they carry meaning (they are [semantic](https://en.wikipedia.org/wiki/Semantics)!).

Your usual build tool will resolve dependencies conflicts based on a version number. 

You want stable releases to be chosen over release candidates, then betas, then alphas releases. You also want versions without `-SNAPSHOT` to take precedence over the SNAPSHOTs.

When a conflict arises, sensible build tools will choose the higher version ([nonsense build tools](https://jakewharton.com/nonsensical-maven-is-still-a-gradle-problem/#the-nonsense) will do something else, but this is another topic). 

The whole Maven ecosystem is based on that premise.

[Sonatype warns about this in their documentation](https://www.sonatype.com/maven-complete-reference/project-object-model#mavenref3-3-1):

```
One gotcha for release version numbers is the ordering of the qualifiers.
Take the version release numbers “1.2.3-alpha-2” and “1.2.3-alpha-10,” 
[...]
Maven is going to sort “alpha-10” before “alpha-2” due to a known issue 
in the way Maven handles version numbers.
```

If build tools were using lexicographical sorting, you could see how SemVer is a problem because `1.0.0-alpha10` would be considered lower than `1.0.0-alpha2`. Not good 💥

Thankfully, Maven 3 (released in 2010) and above have this bug fixed. You can try for yourself using `maven-artifact`:

```kotlin
@file:DependsOn("org.apache.maven:maven-artifact:3.8.6")

import org.apache.maven.artifact.versioning.ComparableVersion

println(ComparableVersion("1.0.0-alpha.10") > ComparableVersion("1.0.0-alpha.2"))
// true
```

Similarly, Gradle has been sorting SemVer versions fine since Gradle 1 (released in 2012) ([test script](https://gist.github.com/martinbonnin/bdbc85d782acf72019661753526292a9))

There are some differences in the implementation, especially around `-dev` versions and case sensitivity. But none of that is relevant if you follow the versioning scheme above. 

If you're curious, you can browse their source code:

* Maven: [ComparableVersion.java](https://github.com/apache/maven/blob/fb6192972092b155ce0d3c9af7fe6b168713d27e/compat/maven-artifact/src/main/java/org/apache/maven/artifact/versioning/ComparableVersion.java)
* Gradle: [StaticVersionComparator.java](https://github.com/gradle/gradle/blob/5bb3182cf38a901dbffbacc0cb9c8efec9f87e9a/platforms/software/dependency-management/src/main/java/org/gradle/api/internal/artifacts/ivyservice/ivyresolve/strategy/StaticVersionComparator.java)

The bottom line is unless you want to support really old build tools (hint: [there's no real reason for this](https://blog.alllex.me/posts/2023-11-03-liberal-library-tooling/)), you can use both SemVer or zero-padding and your dependency resolution will work as expected. 

## The case for SemVer

One strong argument for zero-padding is that it sorts lexicographically. If you have ever [browsed Maven Central](https://repo.maven.apache.org/maven2/), zero-padding makes it easier to find your libs.

On the other hand, SemVer:

* Allows arbitrary numbers of alphas. Want to do `1.0.0-alpha.100`? You can!
* Has a [specification](https://semver.org/).
* More generally, is more consistent. Just like major, minor, and patch versions are not padded, the pre-release version uses the same pattern. 

Both Maven and Gradle have been correctly sorting SemVer versions for **over 14 years**.

The rest of the tooling (HTML indices, anything else?) will improve so that sorting can be made more consistently. But this will only happen if we align on the best practices.

[OkHttp](https://github.com/square/okhttp/tags) uses SemVer, [Apollo](https://github.com/apollographql/apollo-kotlin/releases) too. 

Next time you have to choose a versioning scheme, **consider SemVer**. 

_PS: we should also start our versions at '0', story for another time!_

---

Photo by [Mika Baumeister](https://unsplash.com/photos/white-printing-paper-with-numbers-Wpnoqo2plFA)
      
