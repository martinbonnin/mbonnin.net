---
title: 'Consume your GraphQL API with kotlin coroutines'
excerpt: 'At Dailymotion, we like GraphQL…a lot. We started using it in 2016, we are active contributors to apollo-android, we even have our own…...'
publishDate: 2019-04-23T00:00:00Z
image: '~/assets/images/2019-04-23_Consume-your-GraphQL-API-with-kotlin-coroutines/1*B8UbWOr77VT_-E5DMkZu1g.jpeg'
---

At**Dailymotion, we like GraphQL...a lot. We started using it in 2016, we are active contributors to** [**apollo-android**](https://github.com/apollographql/apollo-android)**, we even have our own server implementation in Python named** [**Tartiflette**](https://github.com/dailymotion/tartiflette)**. When** [**kotlin coroutines**](https://kotlinlang.org/docs/reference/coroutines-overview.html)**became stable** [**at the end of last year,**](https://kotlinlang.org/docs/reference/whatsnew13.html)**we couldn't wait to use them so we added** [**the code**](https://github.com/apollographql/apollo-android/pull/1169)**to do so.**

*** ** * ** ***

GraphQL APIs offer several advantages over traditional [REST APIs](https://developer.dailymotion.com/):

* Clients only download the data they need
* The API is introspectable and self-documented
* Versioning is as easy as deprecating old fields and adding new ones
* Tools like apollo-android and graphiql make a great developer experience

Coroutines offer several advantages over threads/RxJava/(AsyncTasks!):

* Lightweight. No threads are needed to make a suspending function
* Code is easier to read as it is written sequentially
* Exceptions and backtraces are also easier to read since you don't lose the original call site

### Bringing GraphQL and coroutines together

Coroutines support is included in version 1.0.0. In addition to the regular apollo-android dependencies, you will also need \`apollo-coroutines-support\`:

```kotlin
buildscript {
    ext.versions = [
            apolloVersion: "1.0.0"
    ]
    dependencies {
        [...]
        classpath "com.apollographql.apollo:apollo-gradle-plugin:$versions.apolloVersion"
    }
}

repositories {
    maven {
        url 'http://dl.bintray.com/apollographql/android'
    }
}

dependencies {
    implementation "com.apollographql.apollo:apollo-android-support:$versions.apolloVersion"
    implementation "com.apollographql.apollo:apollo-runtime:$versions.apolloVersion"
    implementation "com.apollographql.apollo:apollo-coroutines-support:$versions.apolloVersion"
}
```

Also, add your API schema and GraphQL query to your project:

```graphql
query GithubRepositories(
  $repositoriesCount: Int!
  $orderBy: RepositoryOrderField!
  $orderDirection: OrderDirection!
) {
  viewer {
    repositories(
      first: $repositoriesCount
      orderBy: { field: $orderBy, direction: $orderDirection }
      ownerAffiliations: [OWNER]
    ) {
      nodes {
        ...RepositoryFragment
      }
    }
  }
}

fragment RepositoryFragment on Repository {
  id
  name
  description
}
```

### A simple query

For one-shot queries, Apollo provides the `ApolloQuery.toDeferred` extension function. It will return a [Deferred](https://kotlin.github.io/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-deferred/) and you can call [await](https://kotlin.github.io/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-deferred/await.html)to retrieve the result:

```kotlin
GlobalScope.launch(Dispatchers.Main) {
    val repositoriesQuery = GithubRepositoriesQuery.builder()
            .repositoriesCount(50)
            .orderBy(RepositoryOrderField.UPDATED_AT)
            .orderDirection(OrderDirection.DESC)
            .build()
    val deferred = apolloClient.query(repositoriesQuery).toDeferred()
    
    // .await() will suspend until we get the response
    val response = deferred.await()
    val repositories = response.data()?.viewer()?.repositories()?.nodes()?.map { it.fragments().repositoryFragment() } ?: emptyList()
    repositoriesAdapter.setItems(repositories)
}
```
Compared to [an equivalent](https://gist.github.com/martinbonnin/e3922f19f1e8f55a083cc5cf8919f42d)[RxJava](https://gist.github.com/martinbonnin/e3922f19f1e8f55a083cc5cf8919f42d)[solution](https://gist.github.com/martinbonnin/e3922f19f1e8f55a083cc5cf8919f42d), there's no need for callbacks. The compiler will generate appropriate code and suspend appropriately.

### Error handling

No need for error callbacks either, errors are handled with a try catch:

```kotlin
GlobalScope.launch(Dispatchers.Main) {
  try {
    val repositoriesQuery = GithubRepositoriesQuery.builder()
            .repositoriesCount(50)
            .orderBy(RepositoryOrderField.UPDATED_AT)
            .orderDirection(OrderDirection.DESC)
            .build()
    val response = apolloClient.query(repositoriesQuery).toDeferred().await()
    val repositories = response.data()?.viewer()?.repositories()?.nodes()?.map { it.fragments().repositoryFragment() } 
    repositoriesAdapter.setItems(repositories!!)
  } catch (e: ApolloException) {
    // you will end up here if .await() throws, most likely due to a transport or parsing error
    tvError.visibility = View.VISIBLE
    tvError.text = e.localizedMessage
  } catch (e: NullPointerException) {
    // you will end up here if repositories!! throws above. This will happen if your server sends a response
    // with missing fields or errors
    tvError.visibility = View.VISIBLE
    tvError.text = "Ooops"
  } finally {
    // in all cases, hide the progress bar
    progressBar.visibility = View.GONE
  }
}
```

There are two sources of errors:

* Transport errors will be thrown in `await`. These are most likely unrecoverable.
* Graphql errors won't be thrown by default as some implementations might be able to recover and display partial results.

In all cases, everything reads sequentially, without callbacks.

### A query with cache

If you enabled cache, apollo-android will return two responses. One for the cached data and the other for the network.

For this, Apollo provides the `ApolloQuery.toChannel` extension function. It will return a [channel](https://kotlin.github.io/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.channels/-channel/index.html) that you can iterate on with [consumeEach](https://kotlin.github.io/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.channels/consume-each.html):

```kotlin
channel = apolloClient.query(repositoriesQuery).toChannel()
channel.consumeEach {
  val repositories = it.data()?.viewer()?.repositories()?.nodes()?.map { it.fragments().repositoryFragment() } ?: emptyList()
  repositoriesAdapter.setItems(repositories)
}
```

> Don't forget to cancel the channel if you want to stop listening to updates.

### One last thing

Apollo-android also works for any JVM project, not just Android. The samples are currently taken from Android as it's a big use case right now but everything works on any jvm-based project. So if you're writing your backend in kotlin, you can now use coroutines + graphql as well.

### Wrapup

Consuming your GraphQL API has never been simpler! With the addition of coroutines to handle concurrency and the existing normalized cache and strong typing, GraphQL is a very strong and mature API solution today. Which is no small feat considering the language is still quite young.
> **If you're interested in GraphQL, help us make** [**apollo-android**](https://github.com/apollographql/apollo-android/)**and Tartiflette grow by** [**joining the community**](https://tartiflette.io/)**!**
**Edit 2019--05--27: updated for** [**version 1.0.0**](https://github.com/apollographql/apollo-android/releases/tag/1.0.0)  
[**Tartiflette GraphQL Python Engine · *GraphQL Server implementation built with Python 3.6+***
GraphQL Server implementation built with Python 3.6+tartiflette.](https://tartiflette.io/ "https://tartiflette.io/")[](https://tartiflette.io/) By [Martin Bonnin](https://medium.com/@mbonnin) on [April 23, 2019](https://medium.com/p/8dcf716712b2).

[Canonical link](https://medium.com/@mbonnin/consume-your-graphql-api-with-kotlin-coroutines-8dcf716712b2)

Exported from [Medium](https://medium.com) on November 9, 2024.
