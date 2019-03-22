/**
 * Copyright (c) 2003-2015, CKSource - Frederico Knabben. All rights reserved.
 * For licensing, see LICENSE.md or http://ckeditor.com/license
 */

// This file contains style definitions that can be used by CKEditor plugins.
//
// The most common use for it is the "stylescombo" plugin, which shows a combo
// in the editor toolbar, containing all styles. Other plugins instead, like
// the div plugin, use a subset of the styles on their feature.
//
// If you don't have plugins that depend on this file, you can simply ignore it.
// Otherwise it is strongly recommended to customize this file to match your
// website requirements and design properly.

CKEDITOR.stylesSet.add( 'default', [
	{ name: 'General', element: 'p' },
	{ name: 'Fancy', element: 'p', attributes: {'class': 'JandaQuickNote-normal'} },
	{ name: 'Recipe Introduction', element: 'p', attributes: {'class': 'recipe_intro'} },
	{ name: 'Medium Title', element: 'h3', attributes: {'class': 'JandaQuickNote-normal'} },
	{ name: 'Large Title', element: 'h2', attributes: {'class': 'JandaQuickNote-normal'} },
	{ name: 'a. Bullets', element: 'ol', attributes: {'type': 'a'} },
	{ name: 'i. Bullets', element: 'ol', attributes: {'type': 'i'} },
	{ name: 'Blue Text', element: 'p', attributes: {'class': 'blue_text'} },
] );

