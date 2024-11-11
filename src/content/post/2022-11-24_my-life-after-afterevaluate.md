---
title: 'My life after `afterEvaluate {}`'
excerpt: '...'
publishDate: 2022-11-24T15:00:50.448Z
image: '~/assets/images/2022-11-24_my-life-after-afterevaluate/tjMC7JDDy.png'
---
If you're writing Gradle build scripts, chances are you have already used `afterEvaluate {}`.

This is usually the last resort solution. But in my life of Gradle scripts engineer, I found the odds of `afterEvaluate {}` actually "fixing" your issue are in effect quite high. II guess that explains while you'll still find it in [a lot of places](https://github.com/search?q=afterEvaluate&type=code).

!\[71v4bu.jpg\](https://cdn.hashnode.com/res/hashnode/image/upload/v1669213086874/YOZOmz0N9.jpg align="center")

Because `afterEvaluate {}` postpones your code's execution, it gives more time to other plugins and build logic to execute their "stuff", whatever that is. If you code relies on some of that "stuff" then your build is "fixed" (note all the quotes there).

This is very fragile though for a number of reasons:

* Anyone wanting to use your code now also needs to use `afterEvaluate {}` which is not obvious at all
* Anyone wanting to use the code that uses your code also needs to use `afterEvaluate{}` and so on, all the way down
* It becomes even more complicated as more plugins/scripts are involved
* More generally, it makes dependencies between plugins/scripts implicit and error prone

So how can we make things more solid? The good news is solutions exist!

Usually, `afterEvaluate {}` is required in two occasions:

1. reading extension properties
2. configuring defaults

(if you have more use cases, please reach out, I'm curious to learn about them and will update this article)

## Reading extension properties

Gradle plugins are configured with [extensions](https://docs.gradle.org/current/userguide/custom_plugins.html#sec:getting_input_from_the_build). I won't go into the details of extensions here, the Gradle doc is, as usual, very comprehensive on the matter. The tldr; is that extensions are simple classes that expose options for your plugin. In a sense, it is the public API of your plugin.

This is working well until you need something in your extension to change how the task graph is created. Assume you want to customise the name of your task for an exemple. It doesn't work.

```
open class MyExtension {
  // The name of the person to greet
  var personToGreet: String? = null
}

open class MyPlugin: Plugin<Project> {
  override fun apply(target: Project) {
    val extension = target.extensions.create("myPlugin", MyExtension::class.java)

    // DOES NOT WORK 😞
    // extension.personToGreet is not set here because your 
    // `build.gradle.kts` file is not evaluated yet
    // Your task will be named "greetnull"
    target.tasks.register("greet${extension.personToGreet}") {
      it.doLast {
        println("Hello ${extension.personToGreet}")
      }
    }
  }
}
```

It is tempting to wrap everything in `afterEvaluate{}` and wait for your `build.gradle.kts` to be evaluated but please don't do this for the reasons explained above.

Instead, you can expose a function in your extension. This way, you can execute logic and tweak the task graph from your code. You have full control over when your code executes without relying on the `afterEvaluate {}` chaos:

```
class GreetingOptions {
  // The name of the person to greet
  var personToGreet: String? = null
}

open class MyExtension(val project: Project) {
  fun greeting(action: Action<GreetingOptions>) {
    val options = GreetingOptions()
    action.execute(options)
    
    // WORKS 🤩
    // personToGreet is always set here
    // You have full control of the timing
    project.tasks.register("greet${options.personToGreet}") {
      it.doLast {
        println("Hello ${options.personToGreet}")
      }
    }
  }
}
```

There is one drawback to this solution is that it makes the callsite a bit more verbose:

```
// build.gradle.kts
myPlugin {
  // there's one additional level of nesting here
  greeting {
    personToGreet = "Björn"
  }
}
```

But trust me it's a minor drawback compared to the `afterEvaluate {}` hair pulling especially as your plugin grows, this initial function call will be very small in your total API surface.

## Configuring defaults

The other case is about default behaviour. Sometimes, you don't want your users to specify anything and have valid defaults that can be overridden by the user.

```
apply {
  id("myplugin").version("1.0")
}

// no other configuration, just use defaults
```

This one is trickier. Because there is no extension, there is no function where you can run your code... I've looked at this from every direction and the more I look at this, the more I think you should not support this...

There are ways to do this without `afterEvaluate`. For an example, you could always create the default tasks and then disable them as soon as the extension gets configured. That could work. But this also adds more tasks in `./gradlew --tasks`, more clutter to your build for no obvious reason.

So I _think_ (but I still have to [do it](https://github.com/apollographql/apollo-kotlin/blob/d2ce850a40f9cfa666d111febf2ed3225d6cf4a6/libraries/apollo-gradle-plugin-external/src/main/kotlin/com/apollographql/apollo3/gradle/internal/DefaultApolloExtension.kt#L132)) that forcing the user to opt-in the default is an acceptable workaround here.

```
apply {
  id("myplugin").version("1.0")
}

// One time configuration
myPlugin {
  // opt-in the default behaviour
  greeting()
}
```

Sure it's 3 extra lines and it's not great but in the grand scheme of things, it's a one-time cost that's going to save you a bunch of head-aches over time. And I don't really see another way around.

## Is `afterEvaluate {}` that bad?

Short answer as you guessed is yes!

There is one area though where I find it useful, it's to perform consistency checks. In the example above, it doesn't make sense to force the user to either use the default greeting or define their own.

In these cases, I found it useful. As it's localised to your own code and doesn't introduce timing issues or dependencies with other plugins, it usually works well.

```
abstract class MyPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        val extension = target.extensions.create("myPlugin", MyExtension::class.java, target)
        
        target.afterEvaluate { 
            check(extension.setupDone) {
                """
                    myplugin: you either need to define your greeting or use the default one with `defaultGreeting()`
                """.trimIndent()
            }
        }
    }
}
```

## Conclusion

All in all, whether you trying to read extension properties or provide defaults, I like to think of the entry point to your plugin as a "function" and not just a class. It's something where you can write code. It has drawbacks for sure, it's more verbose and all but once you do that, you can finally say goodbye to that `afterEvaluate {}` chaos and start sailing to new Gradle horizons!
