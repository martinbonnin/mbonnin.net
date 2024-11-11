#!/usr/bin/env kotlin

@file:DependsOn("org.jsoup:jsoup:1.18.1")
@file:DependsOn("com.squareup.okhttp3:okhttp:4.11.0")
@file:DependsOn("com.vladsch.flexmark:flexmark-html2md-converter:0.64.8")
@file:DependsOn("org.jetbrains.kotlinx:kotlinx-datetime-jvm:0.6.1")
@file:DependsOn("com.squareup.okio:okio-jvm:3.9.1")

import com.vladsch.flexmark.html2md.converter.FlexmarkHtmlConverter
import com.vladsch.flexmark.html2md.converter.FlexmarkHtmlConverter.OUTPUT_ATTRIBUTES_ID
import com.vladsch.flexmark.parser.Parser
import com.vladsch.flexmark.util.data.DataHolder
import com.vladsch.flexmark.util.data.MutableDataSet
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalTime
import kotlinx.datetime.atTime
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.OkHttpClient
import okhttp3.Request
import okio.buffer
import okio.sink
import okio.use
import org.jsoup.Jsoup
import java.io.File

val medium = File("../medium")
val okHttpClient = OkHttpClient()


medium.resolve("posts").listFiles()!!.filter { it.extension == "html" && !it.name.startsWith("draft") }
  .sortedBy { it.name }.forEach {
    val slug = it.nameWithoutExtension.dropLast(12).trimEnd('-')
    val images = File("../astrowind/src/assets/images/").resolve(slug)
    val contentBlog = File("../astrowind/src/content/post")

    val markdown = it.toMarkdown(images)
    if (markdown != null) {
      contentBlog.resolve("$slug.md").writeText(markdown)
    }
  }

private fun File.toMarkdown(imagesDir: File): String? {

  return buildString {
    // article
    val document = Jsoup.parse(readText()).body().firstElementChild()!!

    val titleNode = document.selectXpath("header/h1").singleOrNull()
    if (titleNode == null) {
      return null
    }
    val titleText = titleNode.text().trim()
    titleNode.remove()

    val subtitleNode = document.selectXpath("section[@class='p-summary']").singleOrNull()
    if (subtitleNode == null) {
      return null
    }

    val subtitleText = subtitleNode.text().trim()
    subtitleNode.remove()

    val images = document.selectXpath("//img")
    images.forEachIndexed { index, it ->
      val url = it.attributes().get("src")
      downloadImage(url, imagesDir)
      it.attributes().remove("src")
      it.attributes().add("src", "../../assets/images/${imagesDir.name}/${url.name()}")
    }
    val markdown = FlexmarkHtmlConverter.builder(
      MutableDataSet()
        .set(OUTPUT_ATTRIBUTES_ID, false)
    ).build().convert(document)

    appendLine("---")
    appendLine("title: '$titleText'")
    appendLine("excerpt: '${subtitleText}...'")
    val date = Regex("([0-9]+)-([0-9]+)-([0-9]+)_.*").matchEntire(name)!!.groupValues.let {
      LocalDate(it[1].toInt(), it[2].toInt(), it[3].toInt())
    }
    appendLine("publishDate: ${date.atTime(LocalTime(0, 0))}:00Z")
//    appendLine("image: '~/assets/images/${postPublic.name}/thumbnail.$thumbnailExtension'")
    appendLine("---")

    append(markdown)
  }

}

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