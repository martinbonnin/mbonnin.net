---
title: 'Kotlin compatibility QuickSheet'
excerpt: '...'
publishDate: 2021-11-17T15:22:18.030Z
image: '~/assets/images/2021-11-17_kotlin-compatibility-quicksheet/c10XKUx5y.jpeg'
---

> **Edit:** Blog post updated for Kotlin 1.7, see the last paragraph for details.

Kotlin 1.6 has just been released 🎉 ([blog post](https://kotlinlang.org/docs/whatsnew16.html)). This is great news for everyone in the Kotlin ecosystem. As with every feature release, there are new features, new deprecations and other changes that might (but hopefully not too much) break your code.

The [Kotlin documentation](https://kotlinlang.org/docs/) has two awesome pages to go into the implications of new feature releases:

- The [Kotlin evolution - compatibility tools](https://kotlinlang.org/docs/kotlin-evolution.html#compatibility-tools) page
- The [Compatibility modes](https://kotlinlang.org/docs/compatibility-modes.html) page

Additionally, a lot of additional information can be found in the [Kotlin issue tracker](https://youtrack.jetbrains.com/issues), like [this issue about Kotlin native compatibility](https://youtrack.jetbrains.com/issue/KT-42293)

In practice though, I often have a hard time choosing what `apiVersion`, `kotlin-stdlib` version to use, etc... This post is an attempt to list common scenarios to help build a better mental model of what's happening under the hood. And also answer the question of:

Should you use Kotlin 1.6 in a library?

Let's try to answer this question.

_If you prefer reading code than blog posts, the source for this post is available at: https://github.com/martinbonnin/kotlin-compatibility/tree/main_

# project compiled with 1.3 using a lib compiled with 1.6

- `appCompiler=1.3`
- `libCompiler=1.6`

```text
e: /Users/mbonnin/git/kotlin-compatibility/lib-1-6/build/libs/lib-1-6.jar!
/META-INF/lib-1-6.kotlin_module: Module was compiled with an
incompatible version of Kotlin.
The binary version of its metadata is 1.6.0, expected version is 1.1.16.
```

That sounds appropriate. The [evolution principles](https://kotlinlang.org/docs/kotlin-evolution.html#compatibility-flags) state that:

> Preferably (but we can't guarantee it), the binary format is mostly forwards compatible with the next feature release, but not later ones (in the cases when new features are not used, e.g. 1.3 can understand most binaries from 1.4, but not 1.5).

Here, the 1.3 compiler cannot read the 1.6 metadata which sounds expected. Let's try with 1.4

# project compiled with 1.4 using a lib compiled with 1.6

- `appCompiler=1.4`
- `libCompiler=1.6`

```text
> Task :app-1-4:compileKotlin FAILED
e: /Users/mbonnin/git/kotlin-compatibility/lib-1-6/build/libs/lib-1-6.jar!
/META-INF/lib-1-6.kotlin_module: Module was compiled with an
incompatible version of Kotlin.
The binary version of its metadata is 1.6.0, expected version is 1.4.2.
```

Good 😌. This was expected. Note how 1.4 expects 1.4.2 metadata while 1.3 was expecting 1.1.16 so something changed but it's still not enough.

Let's try with 1.5

# project compiled with 1.5 using a lib compiled with 1.6

- `appCompiler=1.5`
- `libCompiler=1.6`

```text
> Task :app-1-5:compileKotlin

BUILD SUCCESSFUL in 5s
```

Huge success 🙌. Everything works as expected.

Now let's assume that we are a library author and we want our new shiny lib to use 1.6 while still allowing 1.3 users. Is that possible?

# Make the lib use apiVersion=1.3, languageVersion=1.3

- `appCompiler=1.3`
- `libCompiler=1.6`
- `libApiVersion=1.3`
- `libLanguageVersion=1.3`

```text
e: Language version 1.3 is no longer supported; please, use version
1.4 or greater.
```

Fair enough. The [1.6 release notes](https://blog.jetbrains.com/kotlin/2021/11/kotlin-1-6-0-is-released/) state that:

> Starting with Kotlin 1.6.0, you can now develop using three previous API versions instead of two (along with the current stable one). Currently, this includes API versions 1.3, 1.4, 1.5, and 1.6.

That doesn't say anything about `languageVersion`(Update: Starting with 1.7, `languageVersion` will also [support three previous versions](https://youtrack.jetbrains.com/issue/KT-49006)). Let's try with just `apiVersion` then:

# Make the lib use apiVersion=1.3, languageVersion=1.6

- `appCompiler=1.3`
- `libCompiler=1.6`
- `libApiVersion=1.3`
- `libLanguageVersion=1.6`

```text
e: /Users/mbonnin/git/kotlin-compatibility/lib-1-6-api-1-3-language-1-6
/build/libs/lib-1-6-api-1-3-language-1-6.jar!/META-INF
/lib-1-6-api-1-3-language-1-6.kotlin_module: Module was compiled
with an incompatible version of Kotlin. The binary version of its
metadata is 1.6.0, expected version is 1.1.16.
```

We're back to step one. The new metadata format cannot be read by the old compiler. Maybe if we could tell the 1.6 compiler to output "backward" compatible metadata that could help. Let's see if `languageVersion=1.4` can help

# Set languageVersion=1.4

- `appCompiler=1.3`
- `libCompiler=1.6`
- `libApiVersion=1.3`
- `libLanguageVersion=1.4`

```text
> Task :lib-1-6-api-1-3-language-1-4:compileKotlin

BUILD SUCCESSFUL in 1s
```

🎉 That worked! So looks like `languageVersion` also affects the metadata format

# Takeaways

As a library author wanting to use Kotlin 1.6, my current understanding is that:

- if your users are compiling against your lib with Kotlin 1.n

  - `languageVersion` should be set to n+1: `languageVersion=1.(n+1)`
  - `apiVersion` doesn't really matter as `kotlin-stdlib` should be resolved to `1.6`, which is backward compatible with any previous `kotlin-stdlib`

- if your users run your lib with a fixed `kotlin-stdlib:1.p` at runtime ([like Gradle](https://blog.mbonnin.net/use-kotlin-15-in-your-gradle-plugins))

  - `apiVersion` should be set to n: `apiVersion=1.p`

If you bump to `1.6` without configuring anything else, your consumers will have to update to Kotlin 1.5.

**Note**: The other way around (backward compatibility?) is a way better story: if you don't bump to `1.6` and keep using `1.5` in your library, then all consumers can upgrade to `1.6` and continue using your lib ([including native ones](https://youtrack.jetbrains.com/issue/KT-42293)).

# Update for Kotlin 1.7

The same is still true. If you bump to Kotlin 1.7 in your lib, your consumers are forced into compiling with 1.6 by default (including for native).

You can keep compatibility with the 1.5 compiler with `languageVersion="1.5"` but that will only go so far because `kotlin-stdlib` itself contains 1.7 metadata so unless you're going to great length to _not_ expose `kotlin-stdlib:1.7` transitively, setting the languageVersion is most likely not going to change much.

**Picture**: [way down](https://flic.kr/p/ogzxmg) by [Romain L](https://www.flickr.com/photos/mr-l/)
