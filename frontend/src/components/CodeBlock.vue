<template>
  <div class="code-block-wrapper relative group my-4 rounded-lg overflow-hidden">
    <button
      @click="copyToClipboard"
      class="absolute top-2 right-2 p-1.5 rounded-md text-xs font-medium transition-colors duration-200 border border-transparent"
      :class="copied ? 'bg-green-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
      aria-label="Copy code"
    >
      <span v-if="copied" class="flex items-center gap-1">
        ✅ Copied!
      </span>
      <span v-else class="flex items-center gap-1">
        📋 Copy
      </span>
    </button>

    <pre><code ref="codeContent" :class="languageClass"><slot /></code></pre>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  code: { type: String, default: '' },
  language: { type: String, default: 'text' }
});

const copied = ref(false);
const codeContent = ref(null);
const languageClass = computed(() => `language-${props.language}`);

const copyToClipboard = async () => {
  try {
    const textToCopy = codeContent.value 
      ? codeContent.value.innerText 
      : props.code;

    await navigator.clipboard.writeText(textToCopy);
    
    copied.value = true;
    setTimeout(() => {
      copied.value = false;
    }, 2000);
  } catch (err) {
    console.error('Failed to copy:', err);
  }
};
</script>

<style scoped>
.code-block-wrapper {
  position: relative;
  background-color: #1e1e1e;
  max-width: 100%;
}
</style>