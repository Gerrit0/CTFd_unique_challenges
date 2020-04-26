declare const $: JQuery;
declare const CTFd: any;
declare const CHALLENGE_ID: number;
declare const ace: any;
declare const flatpickr: any;

interface HTMLElement {
    // Hack, I only use content if I know it exists.
    content: HTMLTemplateElement['content']
}
