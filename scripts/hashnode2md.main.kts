#!/usr/bin/env kotlin

@file:DependsOn("org.jsoup:jsoup:1.18.1")
@file:DependsOn("com.squareup.okhttp3:okhttp:4.11.0")
@file:DependsOn("org.commonmark:commonmark:0.24.0")
@file:DependsOn("org.jetbrains.kotlinx:kotlinx-datetime-jvm:0.6.1")
@file:DependsOn("com.squareup.okio:okio-jvm:3.9.1")
@file:DependsOn("com.squareup.moshi:moshi-kotlin:1.15.1")

import com.squareup.moshi.Moshi
import kotlinx.datetime.Instant
import kotlinx.datetime.TimeZone
import kotlinx.datetime.toLocalDateTime
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.OkHttpClient
import okhttp3.Request
import okio.buffer
import okio.sink
import okio.source
import okio.use
import org.commonmark.node.AbstractVisitor
import org.commonmark.node.Image
import org.commonmark.parser.Parser
import org.commonmark.renderer.markdown.MarkdownRenderer
import java.io.File


fun foo() {
  val medium = File("../hashnode.json").source().buffer().use {
    Moshi.Builder().build().adapter(Any::class.java).fromJson(it)
  }

  check(medium is Map<*, *>)

  val posts = medium.get("posts")
  check(posts is List<*>)

  posts.forEach { post ->
    check(post is Map<*, *>)
    val createdAt = post.get("dateAdded") as String
    var slug = post.get("slug") as String
    val date = Instant.parse(createdAt).toLocalDateTime(TimeZone.UTC)

    slug = String.format("%d-%02d-%02d_$slug", date.year, date.monthNumber, date.dayOfMonth)
    val images = File("../astrowind/src/assets/images/").resolve(slug)
    val contentBlog = File("../astrowind/src/content/post")

    val markdown = post.get("contentMarkdown") as String

    val node = Parser.builder().build().parse(markdown)
    val visitor = object : AbstractVisitor() {
      override fun visit(image: Image?) {
        check(image != null)
        val url = image.destination
        downloadImage(url, images)
        image.destination = "../../assets/images/${slug}/${url.name()}"
        super.visit(image)
      }
    }
    node.accept(visitor)

    val renderer = MarkdownRenderer.builder().build()

    contentBlog.resolve("$slug.md").writeText(
      buildString {
        val title = post.get("title") as String
        val subtitle = post.get("subtitle")
        val coverImage = post.get("coverImage") as String

        downloadImage(coverImage, images)
        appendLine("---")
        appendLine("title: '$title'")
        appendLine("excerpt: '${subtitle}...'")
        appendLine("publishDate: $createdAt")
        appendLine("image: '~/assets/images/${slug}/${coverImage.name()}'")
        appendLine("---")

        append(renderer.render(node))
      }
    )
  }
}

val okHttpClient = OkHttpClient()

foo()


private fun String.name(): String = toHttpUrl().pathSegments.last()


private fun downloadImage(url: String, into: File) {
  val destination = into.resolve(url.name())
  if (destination.exists()) {
    return
  }
  println("downloading $url")
  into.mkdirs()
  Request.Builder()
    .url(url)
    .get()
    .build()
    .let {
      okHttpClient.newCall(it).execute()
    }.let {
      check(it.isSuccessful) {
        "Response not successful"
      }

      it.use { response ->
        destination.sink().buffer().use {
          it.writeAll(response.body!!.source())
        }
      }
    }
}