#!/usr/bin/env kotlin

@file:DependsOn("com.squareup.okio:okio-jvm:3.9.1")
@file:DependsOn("com.squareup.moshi:moshi-kotlin:1.15.1")
@file:DependsOn("org.jetbrains.kotlinx:kotlinx-datetime-jvm:0.6.1")
@file:DependsOn("org.commonmark:commonmark:0.24.0")

import com.squareup.moshi.Moshi
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalTime
import kotlinx.datetime.atTime
import okio.buffer
import okio.source
import okio.use
import org.commonmark.node.AbstractVisitor
import org.commonmark.node.Link
import org.commonmark.node.Node
import org.commonmark.parser.Parser
import org.commonmark.renderer.NodeRenderer
import org.commonmark.renderer.text.TextContentNodeRendererContext
import org.commonmark.renderer.text.TextContentRenderer
import java.io.File


val moshi = Moshi.Builder().build()

File("../skeleton/posts/").listFiles()!!.filter { it.isDirectory }.forEach { postFolder ->
  val slug = postFolder.name
  val images = File("../astrowind/src/assets/images/").resolve(slug)
  images.mkdirs()
  val contentBlog = File("../astrowind/src/content/post")
  val thumbnailExtension = postFolder.listFiles()!!.firstOrNull { it.nameWithoutExtension == "thumbnail" }?.extension
    ?: error("No thumbnail in $postFolder")
  postFolder.listFiles()!!.filter { it.isFile }.forEach { inFile ->
    if (inFile.extension == "mml") {
      contentBlog.resolve("$slug.md").writeText(inFile.toMarkdown(images, thumbnailExtension))
    } else {
      inFile.copyTo(images.resolve(inFile.name), overwrite = true)
    }
  }
}

private fun File.toMarkdown(postPublic: File, thumbnailExtension: String): String {
  return this.source().buffer().use { source ->

    val element = moshi.adapter(Any::class.java).fromJson(source)

    val regex = Regex("([0-9]+)-([0-9]+)-([0-9]+)_.*")
    val matchResult = regex.matchEntire(postPublic.name)
    check(matchResult != null) {
      "Cannot find date in '${postPublic.name}'"
    }

    /**
     * Create a small "excerpt"
     */
    val markdown = source.readUtf8().replace("<!--more-->", "")
    val parser = Parser.builder().build()
    val document = parser.parse(markdown)
    val renderer = TextContentRenderer.Builder().nodeRendererFactory { MyLinkRenderer(it) }.build()
    val text = renderer.render(document).replace("\n", "").replace("\'", "")
    var count = 0
    val excerpt = buildString {
      for (word in text.split(' ')) {
        if (count > 0) {
          append(' ')
        }
        count += word.length
        append(word)

        if (count > 150) {
          break
        }
      }
    }


    check(element is Map<*, *>)
    buildString {
      /**
       * ---
       * title: 'First post'
       * description: 'Lorem ipsum dolor sit amet'
       * pubDate: 'TODO'
       * heroImage: '/blog-placeholder-3.jpg'
       * ---
       *
       */
      appendLine("---")
      appendLine("title: '${element.get("title")}'")
      appendLine("excerpt: '${excerpt}...'")
      val date = matchResult.groupValues.let {
        LocalDate(it[1].toInt(), it[2].toInt(), it[3].toInt())
      }
      appendLine("publishDate: ${date.atTime(LocalTime(0, 0))}:00Z")
      appendLine("image: '~/assets/images/${postPublic.name}/thumbnail.$thumbnailExtension'")
      appendLine("---")

      var inCodeBlock = false
      for (line in markdown.split("\n")) {
        if (line.startsWith("    ")) {
          if (!inCodeBlock) {
            inCodeBlock = true
            appendLine("```")
          }
          appendLine(line.removePrefix("    "))
          continue
        } else {
          if (inCodeBlock) {
            inCodeBlock = false
            appendLine("```")
          }
        }

        var matchResult = Regex("(#+)(.*)(#+)").matchEntire(line)
        if (matchResult != null) {
          appendLine("${matchResult.groupValues.get(1)}${matchResult.groupValues.get(2)}")
          continue
        }

        matchResult = Regex("(.*)]\\((.*)\\)(.*)").matchEntire(line)
        if (matchResult != null) {
          val gv = matchResult.groupValues
          // rewrite images & other local links
          val url = gv.get(2)
          if (!url.startsWith("http")) {
            appendLine("${gv.get(1)}](../../assets/images/${postPublic.name}/${url.trimStart('/')})${gv.get(3)}")
          } else {
            appendLine(line)
          }
          continue
        }

        appendLine(line)
      }
    }
  }
}

/**
 * From https://github.com/commonmark/commonmark-java/issues/166
 */
private class MyLinkRenderer(context: TextContentNodeRendererContext) : AbstractVisitor(), NodeRenderer {
  private val context: TextContentNodeRendererContext = context

  override fun getNodeTypes(): Set<Class<out Node?>?>? {
    return setOf<Class<out Node?>>(Link::class.java)
  }

  override fun render(node: Node) {
    renderChildren(node)
  }

  fun renderChildren(parent: Node) {
    var node: Node? = parent.getFirstChild()
    while (node != null) {
      context.render(node)
      val next: Node? = node.getNext()
      node = next
    }
  }
}