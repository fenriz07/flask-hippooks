/**
 * @license Copyright (c) 2003-2015, CKSource - Frederico Knabben. All rights reserved.
 * For licensing, see LICENSE.md or http://ckeditor.com/license
 */

CKEDITOR.editorConfig = function( config ) {
    config.contentsCss = [
        '/static/css/hipcooks.css',
        '/static/css/bootstrap.min.css',
        '/static/css/MyFontsWebfontsKit.css',
    ];
    // config.removeButtons = 'subscript';

    config.toolbar = [
        ['Source','-','Undo','Redo','-','Scayt'],
        ['Link','Unlink'],
        ['Save','NewPage','Preview','Print','Templates','-','Cut','Copy','Paste'],
        '/',
        ['Bold','Italic','Underline','Strike'],
        ['NumberedList','BulletedList','-','Outdent','Indent'],
        ['JustifyLeft','JustifyCenter','JustifyRight','JustifyBlock'],
        ['Image','Table','SpecialChar'],
        ['FontSize','TextColor','Styles'],
    ];
};
